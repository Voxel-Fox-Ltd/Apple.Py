import json
import io
import zlib
import re
import os

import discord
from discord.ext import commands
import voxelbotutils as utils


class SphinxObjectFileReader(object):
    # Inspired by Sphinx's InventoryFileReader
    BUFSIZE = 16 * 1024

    def __init__(self, buffer):
        self.stream = io.BytesIO(buffer)

    def readline(self):
        return self.stream.readline().decode('utf-8')

    def skipline(self):
        self.stream.readline()

    def read_compressed_chunks(self):
        decompressor = zlib.decompressobj()
        while True:
            chunk = self.stream.read(self.BUFSIZE)
            if len(chunk) == 0:
                break
            yield decompressor.decompress(chunk)
        yield decompressor.flush()

    def read_compressed_lines(self):
        buf = b''
        for chunk in self.read_compressed_chunks():
            buf += chunk
            pos = buf.find(b'\n')
            while pos != -1:
                yield buf[:pos].decode('utf-8')
                buf = buf[pos + 1:]
                pos = buf.find(b'\n')


class LibraryDocs(utils.Cog):

    DISCORDJS_DOCS = None

    def __init__(self, bot:utils.Bot):
        super().__init__(bot)
        self._rtfm_cache = {}  # {library: {class_or_method: url_to_doc}}

    @utils.Cog.listener()
    async def on_message(self, message:discord.Message):
        """
        Listens for "vbu.git" and responds with a Git url.
        """

        if message.author.bot:
            return
        if message.content.lower() != "vbu.git":
            return
        try:
            return await message.channel.send("<https://github.com/Voxel-Fox-Ltd/VoxelBotUtils/>")
        except Exception:
            pass

    def get_embed_from_cache(self, cache, obj) -> dict:
        """
        Build up some kwargs from the cache and a given input object.
        """

        item_casefold = obj.casefold()
        split = item_casefold.split('.')
        outputs = []

        for key, link in cache.items():

            # Key would be something like 'TextChannel.fetch', now 'textchannel.fetch'
            key_casefold = key.casefold()

            # See if we got an exact match
            if item_casefold in key_casefold:
                if item_casefold == key_casefold:
                    outputs.append((key, link, 20,))
                else:
                    outputs.append((key, link, 15,))

            # See if we're looking for a method
            if len(split) == 1:
                continue

            # Search by method
            if split[1] and split[1] in key_casefold:
                if split[1] == key_casefold:
                    outputs.append((key, link, 12,))
                else:
                    outputs.append((key, link, 10,))

            # Search by class
            if split[0] and split[0] in key_casefold:
                if split[0] == key_casefold:
                    outputs.append((key, link, 7,))
                else:
                    outputs.append((key, link, 5,))

        # Hey maybe they didn't say anything useful
        if len(outputs) == 0:
            return {"content": "I couldn't find anything. Sorry."}

        # Yo there's a result. Let's embed that.
        embed = utils.Embed(use_random_colour=True)
        outputs.sort(key=lambda i: (i[2], i[0]), reverse=True)
        embed.description = ""
        for key, url, weight in outputs:
            v = f"[`{key}`]({url})\n"
            if v in embed.description:
                continue
            embed.description += v
            if embed.description.count("\n") >= 8:
                break
        return {"embed": embed}

    async def get_discordjs_docs(self):
        """
        Get the DiscordJS documentation from their Github page.
        """

        async with self.bot.session.get("https://raw.githubusercontent.com/discordjs/discord.js/docs/stable.json") as r:
            body = await r.text()
        data = json.loads(body)

        cache = {}

        for clazz in data['classes']:
            cache[clazz['name']] = f"https://discord.js.org/#/docs/main/stable/class/{clazz['name']}"
            for p in clazz.get('props', list()) + clazz.get('methods', list()):
                if p['name'].startswith('_'):
                    continue
                cache[f"{clazz['name']}.{p['name']}"] = f"https://discord.js.org/#/docs/main/stable/class/{clazz['name']}?scrollTo={p['name']}"

        for clazz in data['typedefs']:
            cache[clazz['name']] = f"https://discord.js.org/#/docs/main/stable/typedef/{clazz['name']}"
            for p in clazz.get('props', list()) + clazz.get('methods', list()):
                if p['name'].startswith('_'):
                    continue
                cache[f"{clazz['name']}.{p['name']}"] = f"https://discord.js.org/#/docs/main/stable/typedef/{clazz['name']}?scrollTo={p['name']}"

        self._rtfm_cache['djs'] = cache

    async def get_jda_docs(self):
        """
        Get the DiscordJS documentation from their Github page.
        """

        async with self.bot.session.get("https://ci.dv8tion.net/job/JDA/javadoc/member-search-index.js") as r:
            body = await r.text()
        data = json.loads(body.split("=", 1)[-1].strip())

        cache = {}

        for item in data:
            cache[f"{item['c']}"] = f"https://ci.dv8tion.net/job/JDA/javadoc/{item['p'].replace('.', '/')}.html"
            cache[f"{item['c']}.{item['l'].split('(')[0]}"] = f"https://ci.dv8tion.net/job/JDA/javadoc/{item['p'].replace('.', '/')}.html#{item['url']}"

        self._rtfm_cache['jda'] = cache

    def parse_object_inv(self, stream, url):
        # key: URL
        # n.b.: key doesn't have `discord` or `discord.ext.commands` namespaces
        result = {}

        # first line is version info
        inv_version = stream.readline().rstrip()

        if inv_version != '# Sphinx inventory version 2':
            raise RuntimeError('Invalid objects.inv file version.')

        # next line is "# Project: <name>"
        # then after that is "# Version: <version>"
        projname = stream.readline().rstrip()[11:]
        version = stream.readline().rstrip()[11:]

        # next line says if it's a zlib header
        line = stream.readline()
        if 'zlib' not in line:
            raise RuntimeError('Invalid objects.inv file, not z-lib compatible.')

        # This code mostly comes from the Sphinx repository.
        entry_regex = re.compile(r'(?x)(.+?)\s+(\S*:\S*)\s+(-?\d+)\s+(\S+)\s+(.*)')
        for line in stream.read_compressed_lines():
            match = entry_regex.match(line.rstrip())
            if not match:
                continue

            name, directive, prio, location, dispname = match.groups()
            domain, _, subdirective = directive.partition(':')
            if directive == 'py:module' and name in result:
                continue

            # Most documentation pages have a label
            if directive == 'std:doc':
                subdirective = 'label'

            if location.endswith('$'):
                location = location[:-1] + name

            key = name if dispname == '-' else dispname
            prefix = f'{subdirective}:' if domain == 'std' else ''

            if projname == 'discord.py':
                key = key.replace('discord.ext.commands.', '').replace('discord.', '')

            result[f'{prefix}{key}'] = os.path.join(url, location)

        return result

    async def build_rtfm_lookup_table(self, page_types):
        cache = {}
        for key, page in page_types.items():
            cache[key] = {}
            async with self.bot.session.get(page + '/objects.inv') as resp:
                if resp.status != 200:
                    raise RuntimeError('Cannot build rtfm lookup table, try again later.')
                stream = SphinxObjectFileReader(await resp.read())
                cache[key] = self.parse_object_inv(stream, page)
        self._rtfm_cache = cache

    async def do_rtfm(self, ctx, key, obj):
        """
        Check docs, generate and send output.
        """

        page_types = {
            'latest': 'https://discordpy.readthedocs.io/en/latest',
            'python': 'https://docs.python.org/3',
            'pygame': 'https://www.pygame.org/docs',
            'voxelbotutils': 'https://voxelbotutils.readthedocs.io/en/latest/',
        }
        non_sphinx_page_types = {
            'djs': self.get_discordjs_docs,
            'jda': self.get_jda_docs,
        }

        # Make sure we got something
        if obj is None:
            return

        # See if we have an rtfm cache
        if not self._rtfm_cache:
            await ctx.trigger_typing()
            await self.build_rtfm_lookup_table(page_types)
            for i in non_sphinx_page_types.values():
                await i()

        obj = re.sub(r'^(?:discord\.(?:ext\.)?)?(?:commands\.)?(.+)', r'\1', obj)

        # point the discord.abc.Messageable types properly
        if key == 'latest':
            q = obj.lower()
            for name in dir(discord.abc.Messageable):
                if name[0] == '_':
                    continue
                if q == name:
                    obj = f'abc.Messageable.{name}'
                    break

        return await ctx.send(**self.get_embed_from_cache(self._rtfm_cache[key], obj))

    @utils.group()
    async def rtfm(self, ctx):
        """
        Get some data from the docs.
        """

        pass

    @rtfm.command(name="djs")
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def rtfm_djs(self, ctx:utils.Context, *, item:str):
        """
        Get an item from the Discord.js documentation.
        """

        await self.do_rtfm(ctx, "djs", item)

    @rtfm.command(name="jda")
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def rtfm_jda(self, ctx:utils.Context, *, item:str):
        """
        Get an item from the Discord.js documentation.
        """

        await self.do_rtfm(ctx, "jda", item)


    @rtfm.command(name="dpy")
    async def rtdm_dpy(self, ctx, *, obj:str):
        """
        Gives you a documentation link for a discord.py entity.
        Events, objects, and functions are all supported through a
        a cruddy fuzzy algorithm.
        """

        await self.do_rtfm(ctx, "latest", obj)

    @rtfm.command(name="vbu")
    async def rtdm_vbu(self, ctx, *, obj:str):
        """
        Gives you a documentation link for a discord.py entity.
        Events, objects, and functions are all supported through a
        a cruddy fuzzy algorithm.
        """

        await self.do_rtfm(ctx, "voxelbotutils", obj)

    @rtfm.command(name="python", aliases=["py"])
    async def rtdm_python(self, ctx, *, obj:str):
        """
        Gives you a documentation link for a Python entity.
        """

        await self.do_rtfm(ctx, "python", obj)

    @rtfm.command(name="pygame")
    async def rtdm_pygame(self, ctx, *, obj:str):
        """
        Gives you a documentation link for a Python entity.
        """

        await self.do_rtfm(ctx, "pygame", obj)


def setup(bot:utils.Bot):
    x = LibraryDocs(bot)
    bot.add_cog(x)
