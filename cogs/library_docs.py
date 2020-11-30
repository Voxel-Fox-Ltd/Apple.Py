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

    async def get_discordjs_docs(self):
        """
        Get the DiscordJS documentation from their Github page.
        """

        if self.DISCORDJS_DOCS is not None:
            return self.DISCORDJS_DOCS

        async with self.bot.session.get("https://raw.githubusercontent.com/discordjs/discord.js/docs/stable.json") as r:
            body = await r.text()
        data = json.loads(body)

        cache = {}

        for clazz in data['classes']:
            cache[clazz['name']] = f"class/{clazz['name']}"
            for p in clazz.get('props', list()) + clazz.get('methods', list()):
                if p['name'].startswith('_'):
                    continue
                cache[f"{clazz['name']}.{p['name']}"] = f"class/{clazz['name']}?scrollTo={p['name']}"

        for clazz in data['typedefs']:
            cache[clazz['name']] = f"typedef/{clazz['name']}"
            for p in clazz.get('props', list()) + clazz.get('methods', list()):
                if p['name'].startswith('_'):
                    continue
                cache[f"{clazz['name']}.{p['name']}"] = f"typedef/{clazz['name']}?scrollTo={p['name']}"

        self.DISCORDJS_DOCS = cache
        return self.DISCORDJS_DOCS

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
                # From the Sphinx Repository:
                # due to a bug in 1.1 and below,
                # two inventory entries are created
                # for Python modules, and the first
                # one is correct
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
            sub = cache[key] = {}
            async with self.bot.session.get(page + '/objects.inv') as resp:
                if resp.status != 200:
                    raise RuntimeError('Cannot build rtfm lookup table, try again later.')

                stream = SphinxObjectFileReader(await resp.read())
                cache[key] = self.parse_object_inv(stream, page)

        self._rtfm_cache = cache

    async def do_rtfm(self, ctx, key, obj):
        page_types = {
            'latest': 'https://discordpy.readthedocs.io/en/latest',
            'python': 'https://docs.python.org/3',
        }

        if obj is None:
            await ctx.send(page_types[key])
            return

        if not hasattr(self, '_rtfm_cache'):
            await ctx.trigger_typing()
            await self.build_rtfm_lookup_table(page_types)

        obj = re.sub(r'^(?:discord\.(?:ext\.)?)?(?:commands\.)?(.+)', r'\1', obj)

        if key.startswith('latest'):
            # point the abc.Messageable types properly:
            q = obj.lower()
            for name in dir(discord.abc.Messageable):
                if name[0] == '_':
                    continue
                if q == name:
                    obj = f'abc.Messageable.{name}'
                    break

        item_casefold = obj.casefold()
        split = item_casefold.split('.')
        outputs = []

        for key, link in self._rtfm_cache[key].items():
            key_casefold = key.casefold()
            if item_casefold in key_casefold:
                if item_casefold == key_casefold:
                    outputs.append((key, link, 20,))
                else:
                    outputs.append((key, link, 10,))
            if len(split) == 1:
                continue
            if split[0] in key_casefold:
                outputs.append((key, link, 5,))
            if split[1] in key_casefold:
                outputs.append((key, link, 3,))

        embed = utils.Embed(use_random_colour=True)
        if len(outputs) == 0:
            return await ctx.send('Could not find anything. Sorry.')

        outputs.sort(key=lambda i: (i[2], i[0]), reverse=True)
        embed.description = '\n'.join(f'[`{key}`]({url})' for key, url, _ in outputs[:8])
        await ctx.send(embed=embed)

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

        item_casefold = item.casefold()
        split = item_casefold.split('.')
        docs = await self.get_discordjs_docs()
        outputs = []

        for key, link in docs.items():
            key_casefold = key.casefold()
            if item_casefold in key_casefold:
                if item_casefold == key_casefold:
                    outputs.append((key, link, 20,))
                else:
                    outputs.append((key, link, 10,))
            if len(split) == 1:
                continue
            if split[0] in key_casefold:
                outputs.append((key, link, 5,))
            if split[1] in key_casefold:
                outputs.append((key, link, 3,))

        outputs.sort(key=lambda i: (i[2], i[0]), reverse=True)
        embed = utils.Embed(use_random_colour=True)
        description = ""
        for line in outputs[:8]:
            description += f"[`{line[0]}`](https://discord.js.org/#/docs/main/stable/{line[1]})\n"
        embed.description = description
        if not description:
            return await ctx.send('Could not find anything. Sorry.')
        await ctx.send(embed=embed)

    @rtfm.command(name="dpy")
    async def rtdm_dpy(self, ctx, *, obj:str):
        """
        Gives you a documentation link for a discord.py entity.
        Events, objects, and functions are all supported through a
        a cruddy fuzzy algorithm.
        """

        await self.do_rtfm(ctx, "latest", obj)

    @rtfm.command(name="python", aliases=["py"])
    async def rtdm_python(self, ctx, *, obj:str):
        """
        Gives you a documentation link for a Python entity.
        """

        await self.do_rtfm(ctx, "python", obj)


def setup(bot:utils.Bot):
    x = LibraryDocs(bot)
    bot.add_cog(x)
