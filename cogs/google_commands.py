import voxelbotutils as utils


class GoogleCommands(utils.Cog):

    @utils.command()
    @utils.checks.is_config_set('api_keys', 'google', 'search_engine_id')
    @utils.checks.is_config_set('api_keys', 'google', 'api_key')
    async def google(self, ctx:utils.Context, *, query:str):
        """
        Search a query on Google.
        """

        params = {
            'key': self.bot.config['api_keys']['google']['api_key'],
            'cx': self.bot.config['api_keys']['google']['search_engine_id'],
            'num': 5,
            'q': query,
            'safe': 'active',
        }
        async with self.bot.session.get("https://customsearch.googleapis.com/customsearch/v1", params=params) as r:
            data = await r.json()
        with utils.Embed(use_random_colour=True) as embed:
            ENDL = '\n'
            for d in data['items']:
                embed.add_field(d['title'][:256], f"[{d['displayLink']}]({d['link']}) - {d['snippet'].replace(ENDL, ' ')}", inline=False)
        await ctx.send(embed=embed)


def setup(bot:utils.Bot):
    x = GoogleCommands(bot)
    bot.add_cog(x)
