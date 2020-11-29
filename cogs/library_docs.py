import voxelbotutils as utils


class LibraryDocs(utils.Cog):

    DISCORDJS_DOCS = None

    async def get_discordjs_docs(self):
        """
        Get the DiscordJS documentation from their Github page.
        """

        if self.DISCORDJS_DOCS is not None:
            return self.DISCORDJS_DOCS

        async with self.bot.session.get("https://raw.githubusercontent.com/discordjs/discord.js/docs/stable.json") as r:
            data = await r.json()

        cache = {}

        for clazz in data['classes']:
            cache[clazz['name']] = clazz['name']
            for p in clazz.get('props', list()) + clazz.get('methods', list()):
                if p['name'].startswith('_'):
                    continue
                cache[f"{clazz['name']}.{p['name']}"] = f"class/{clazz['name']}?scrollTo={p['name']}"

        for clazz in data['interfaces']:
            cache[clazz['name']] = clazz['name']
            for p in clazz.get('props', list()) + clazz.get('methods', list()):
                if p['name'].startswith('_'):
                    continue
                cache[f"{clazz['name']}.{p['name']}"] = f"typedef/{clazz['name']}?scrollTo={p['name']}"

        self.DISCORDJS_DOCS = cache
        return self.DISCORDJS_DOCS

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

        split = item.split('.')
        docs = await self.get_discordjs_docs()
        outputs = []
        for key, link in docs:
            if item in key:
                outputs.append((key, link, 10,))
            if len(split) == 1:
                continue
            if split[0] in key:
                outputs.append((key, link, 5,))
            if split[1] in key:
                outputs.append((key, link, 3,))
        outputs.sort(lambda i: i[-1])
        embed = utils.Embed(use_random_colour=True)
        description = ""
        for line in outputs[:10]:
            description += f"[`{line[0]}`](https://discord.js.org/#/docs/main/stable/{line[1]})\n"
        emebd.description = description
        await ctx.send(embed=emebd)


def setup(bot:utils.Bot):
    x = LibraryDocs(bot)
    bot.add_cog(x)
