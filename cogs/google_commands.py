import voxelbotutils as utils


class GoogleCommands(utils.Cog):

    def get_search_page(self, query:str):
        """
        Get a number of results from Google
        """

        async def wrapper(page_number:int):
            params = {
                'key': self.bot.config['api_keys']['google']['api_key'],
                'cx': self.bot.config['api_keys']['google']['search_engine_id'],
                'num': 3,
                'q': query,
                'safe': 'active',
                'start': 3 * page_number,
            }
            async with self.bot.session.get("https://customsearch.googleapis.com/customsearch/v1", params=params) as r:
                data = await r.json()
            ENDL = '\n'
            output_data = []
            for d in data['items']:
                output_data.append((d['title'][:256], f"[{d['displayLink']}]({d['link']}) - {d['snippet'].replace(ENDL, ' ')}"))
            return output_data

        return wrapper

    @utils.command()
    @utils.checks.is_config_set('api_keys', 'google', 'search_engine_id')
    @utils.checks.is_config_set('api_keys', 'google', 'api_key')
    async def google(self, ctx:utils.Context, *, query:str):
        """
        Search a query on Google.
        """

        def formatter(menu, data):
            embed = utils.Embed(use_random_colour=True)
            for d in data:
                embed.add_field(*d, inline=False)
            embed.set_footer(f"Page {menu.current_page + 1}")
            return embed
        await utils.Paginator(self.get_search_page(query), formatter=formatter).start(ctx)


def setup(bot:utils.Bot):
    x = GoogleCommands(bot)
    bot.add_cog(x)
