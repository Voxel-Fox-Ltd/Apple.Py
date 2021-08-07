import json
import io
import zlib
import re
import os
import textwrap
import unicodedata

import discord
from discord.ext import commands
import voxelbotutils as vbu


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


class LibraryDocs(vbu.Cog):

    DISCORDJS_DOCS = None

    def __init__(self, bot: vbu.Bot):
        super().__init__(bot)
        self._rtfm_cache = {}  # {library: {class_or_method: url_to_doc}}

    @vbu.Cog.listener()
    async def on_message(self, message: discord.Message):
        """
        Listens for "vbu.git" and responds with a Git url or "vbu.docs" to respond with a readthedocs url.
        """

        if message.author.bot:
            return

        possible_links = {
            "vbu.git": "https://github.com/Voxel-Fox-Ltd/VoxelBotvbu/",
            "vbu.docs": "https://voxelbotvbu.readthedocs.io/en/latest/"
        }

        if message.content.lower() not in possible_links.keys():
            return
        try:
            return await message.channel.send(f"<{possible_links[message.content.lower()]}>")
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
        embed = vbu.Embed(use_random_colour=True)
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
        Get the JDA documentation from their docs
        """

        async with self.bot.session.get("https://ci.dv8tion.net/job/JDA/javadoc/member-search-index.js") as r:
            body = await r.text()
        data = json.loads(body.split("=", 1)[-1].split(';')[0].strip())

        cache = {}

        for item in data:
            cache[f"{item['c']}"] = f"https://ci.dv8tion.net/job/JDA/javadoc/{item['p'].replace('.', '/')}/{item['c']}.html"
            if item['l'].startswith(item['c']):
                continue
            cache[f"{item['c']}.{item['l'].split('(')[0]}"] = f"https://ci.dv8tion.net/job/JDA/javadoc/{item['p'].replace('.', '/')}/{item['c']}.html#{item.get('url', item.get('l'))}"

        self._rtfm_cache['jda'] = cache

    async def get_java_docs(self):
        """
        Get the Java docs from there JSON docs
        """

        async with self.bot.session.get("https://docs.oracle.com/en/java/javase/15/docs/api/member-search-index.js") as r:
            body = await r.text()
        data = json.loads(body.split("=", 1)[-1].split(';')[0].strip())

        cache = {}

        for item in data:
            cache[f"{item['c']}"] = f"https://ci.dv8tion.net/job/JDA/javadoc/{item['p'].replace('.', '/')}/{item['c']}.html"
            if item['l'].startswith(item['c']):
                continue
            cache[f"{item['c']}.{item['l'].split('(')[0]}"] = f"https://docs.oracle.com/en/java/javase/15/docs/api/java.base/{item['p'].replace('.', '/')}/{item['c']}.html#{item.get('url', item.get('l'))}"

        self._rtfm_cache['java'] = cache

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
        _ = stream.readline().rstrip()[11:]

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
            if projname.lower() == 'voxelbotvbu':
                display_key = f'{prefix}{key}'
                if display_key.startswith("voxelbotvbu.cogs.vbu."):
                    continue
                elif display_key.startswith("label:"):
                    direct_location = os.path.join(url, location)
                    if "/apireference.html" in direct_location:
                        continue
                    elif "/changelog.html" in direct_location:
                        continue
                    elif "/py-modindex.html" in direct_location:
                        continue
                    elif "/genindex.html" in direct_location:
                        continue
                    elif "/search.html" in direct_location:
                        continue

            result[f'{prefix}{key}'] = os.path.join(url, location)

        return result

    async def build_rtfm_lookup_table(self, page_types):
        cache = {}
        for key, page in page_types.items():
            cache[key] = {}
            async with self.bot.session.get(page + '/objects.inv') as r:
                if not r.ok:
                    message = await r.read()
                    raise RuntimeError(f"Cannot build rtfm lookup table - {message}")
                stream = SphinxObjectFileReader(await r.read())
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
            'voxelbotvbu': 'https://voxelbotvbu.readthedocs.io/en/latest',
        }
        non_sphinx_page_types = {
            'djs': self.get_discordjs_docs,
            'jda': self.get_jda_docs,
            'java': self.get_java_docs,
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

    @vbu.command(aliases=['dedent'])
    async def unindent(self, ctx: vbu.Context, message: discord.Message):
        """
        Unindents the codeblock inside of a message.
        """

        codeblock_backtick_count = message.content.count('```')
        if codeblock_backtick_count == 0:
            return await ctx.send("There aren't any codeblocks in that message.")
        elif codeblock_backtick_count % 2 == 1:
            return await ctx.send("The codeblocks in that message are a bit messed up.")
        elif codeblock_backtick_count == 2:
            pass
        else:
            return await ctx.send("I can only unindent messages with one codeblock.")
        block_match = re.search(r"```(.+)\n([\s\S]+)\n```", message.content)
        if not block_match:
            return await ctx.send("I couldn't regex that message for codeblocks.")
        return await ctx.send(f"```{block_match.group(1)}\n{textwrap.dedent(block_match.group(2))}\n```")

    @vbu.group()
    async def rtfm(self, ctx):
        """
        Get some data from the docs.
        """

        pass

    @rtfm.command(name="djs")
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def rtfm_djs(self, ctx: vbu.Context, *, item: str):
        """
        Get an item from the Discord.js documentation.
        """

        await self.do_rtfm(ctx, "djs", item)

    @rtfm.command(name="jda")
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def rtfm_jda(self, ctx: vbu.Context, *, item: str):
        """
        Get an item from the JDA documentation.
        """

        await self.do_rtfm(ctx, "jda", item)

    @rtfm.command(name="java")
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def rtfm_java(self, ctx: vbu.Context, *, item: str):
        """
        Get an item from the Java documentation.
        """

        await self.do_rtfm(ctx, "java", item)

    @rtfm.command(name="dpy")
    async def rtdm_dpy(self, ctx, *, obj: str):
        """
        Gives you a documentation link for a discord.py entity.
        Events, objects, and functions are all supported through a
        a cruddy fuzzy algorithm.
        """

        await self.do_rtfm(ctx, "latest", obj)

    @rtfm.command(name="vbu")
    async def rtdm_vbu(self, ctx, *, obj: str):
        """
        Gives you a item from the docs of VoxelBotvbu
        """

        await self.do_rtfm(ctx, "voxelbotvbu", obj)

    @rtfm.command(name="python", aliases=["py"])
    async def rtdm_python(self, ctx, *, obj: str):
        """
        Gives you a documentation link for a Python entity.
        """

        await self.do_rtfm(ctx, "python", obj)

    @rtfm.command(name="pygame")
    async def rtdm_pygame(self, ctx, *, obj: str):
        """
        Gives you a documentation link for a PyGame entity.
        """

        await self.do_rtfm(ctx, "pygame", obj)

    @rtfm.command(name="js", aliases=['javascript'])
    async def rtdm_js(self, ctx, *, obj: str):
        """
        Gives you a documentation link for a Javascript entity.
        """

        url = "https://developer.mozilla.org/api/v1/search"
        params = {
            'q': obj,
            'local': 'en-US',
        }
        headers = {
            'User-Agent': self.bot.user_agent,
        }
        async with self.bot.session.get(url, params=params, headers=headers) as r:
            data = await r.json()
        if not data['documents']:
            return await ctx.send("I couldn't find anything. Sorry.")
        embed = vbu.Embed(use_random_colour=True, description="")
        for i in data['documents']:
            if 'web/javascript' not in i['slug']:
                continue
            embed.description += f"[`{i['title']}`](https://developer.mozilla.org{i['mdn_url']})\n"
            if embed.description.count("\n") >= 8:
                break
        return await ctx.send(embed=embed)

    @rtfm.command(name="dotnet", aliases=['.net'])
    async def rtdm_dotnet(self, ctx, *, obj: str):
        """
        Gives you a documentation link for a Javascript entity.
        """

        url = "https://docs.microsoft.com/api/apibrowser/dotnet/search"
        params = {
            'api-version': '0.2',
            'search': obj,
            'locale': 'en-us',
            '$filter': "monikers/any(t: t eq 'net-5.0')",
        }
        headers = {
            'User-Agent': self.bot.user_agent,
        }
        async with self.bot.session.get(url, params=params, headers=headers) as r:
            data = await r.json()
        if not data['results']:
            return await ctx.send("I couldn't find anything. Sorry.")
        embed = vbu.Embed(use_random_colour=True, description="")
        for i in data['results']:
            embed.description += f"[`{i['displayName']}`]({i['url']})\n"
            if embed.description.count("\n") >= 8:
                break
        return await ctx.send(embed=embed)

    @vbu.command(aliases=['pip'])
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def pypi(self, ctx: vbu.Context, module: commands.clean_content):
        """
        Grab data from PyPi.
        """

        # Get data
        async with self.bot.session.get(f"https://pypi.org/pypi/{module}/json") as r:
            if r.status != 200:
                with vbu.Embed(use_random_colour=True) as embed:
                    embed.title = f"Module `{module}` not found"
                    embed.description = f"[Search Results](https://pypi.org/search/?q={module})"
                return await ctx.send(embed=embed)
            data = await r.json()

        # Format into an embed
        with vbu.Embed(use_random_colour=True) as embed:
            embed.set_author(name=data['info']['name'], url=f"https://pypi.org/project/{module}")
            embed.description = data['info']['summary']
        return await ctx.send(embed=embed)

    @vbu.command(aliases=['npmjs'])
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def npm(self, ctx: vbu.Context, package_name: str):
        """
        Check NPM for a package.
        """

        # Get our data
        async with self.bot.session.get(f"http://registry.npmjs.com/{package_name}/") as e:
            if e.status == 404:
                await ctx.send(f"I could not find anything about `{package_name}` :c")
                return
            if e.status != 200:
                await ctx.send("Something went wrong, try again later...")
                return
            data = await e.json()

        # make a lil embed
        with vbu.Embed(use_random_colour=True) as embed:
            embed.set_author(name=data['name'], url=f"https://www.npmjs.com/package/{package_name}")
            embed.description = data['description']
        await ctx.send(embed=embed)

    @vbu.command()
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def nuget(self, ctx: vbu.Context, package_name: str):
        """
        Check nuget for a package.
        """

        # Get our data
        async with self.bot.session.get(f"https://azuresearch-usnc.nuget.org/query?q={package_name}") as e:
            if e.status != 200:
                await ctx.send("Something went wrong, try again later...")
                return
            data = await e.json()

        # make a lil embed
        with vbu.Embed(use_random_colour=True) as embed:
            if data['data']:
                embed.set_author(name=data['data'][0]['title'], url=f"https://www.nuget.org/packages/{data['data'][0]['id']}")
                embed.description = data['data'][0]['description']
            else:
                await ctx.send(f"I could not find anything for `{package_name}` :c")
                return
        await ctx.send(embed=embed)

    @vbu.command()
    @commands.bot_has_permissions(send_messages=True)
    async def charinfo(self, ctx, *, characters: str):
        """
        Shows you information about a number of characters.
        """

        def to_string(c):
            digit = f'{ord(c):x}'
            name = unicodedata.name(c, 'Name not found.')
            return f'`\\U{digit:>08}`: {name} - {c} \N{EM DASH} <http://www.fileformat.info/info/unicode/char/{digit}>'
        msg = '\n'.join(map(to_string, characters))
        if len(msg) > 2000:
            return await ctx.send('Output too long to display.')
        await ctx.send(msg)

    @vbu.command(add_slash_command=False)
    async def getinterval(self, ctx: vbu.Context, message1: int, message2: int):
        """
        Get the interval between two snowflakes.
        """

        timestamps = sorted([discord.Object(message1).created_at, discord.Object(message2).created_at], reverse=True)
        return await ctx.send(timestamps[0] - timestamps[1])


def setup(bot:vbu.Bot):
    x = LibraryDocs(bot)
    bot.add_cog(x)
