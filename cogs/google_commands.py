import voxelbotutils as utils


class GoogleCommands(utils.Cog):

    def get_search_page(self, query:str, num:int, image:bool=False):
        """
        Get a number of results from Google
        """

        async def wrapper(page_number:int):
            params = {
                'key': self.bot.config['api_keys']['google']['api_key'],
                'cx': self.bot.config['api_keys']['google']['search_engine_id'],
                'num': num,
                'q': query,
                'safe': 'active',
                'start': num * page_number,
            }
            if image:
                params.update({'searchType': 'image'})
                formatter = lambda d: (
                    d['title'][:256],
                    d['link']
                )
            else:
                formatter = lambda d: (
                    d['title'][:256],
                    f"[{d['displayLink']}]({d['link']}) - {d['snippet'].replace(ENDL, ' ')}"
                )
            async with self.bot.session.get("https://customsearch.googleapis.com/customsearch/v1", params=params) as r:
                data = await r.json()
            ENDL = '\n'
            output_data = []
            for d in data.get('items', list()):
                output_data.append(formatter(d))
            return output_data

        return wrapper

    @utils.group(invoke_without_command=True)
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
        await utils.Paginator(self.get_search_page(query, 3), formatter=formatter).start(ctx)

    @google.command(name='images', aliases=['image', 'i'])
    @utils.checks.is_config_set('api_keys', 'google', 'search_engine_id')
    @utils.checks.is_config_set('api_keys', 'google', 'api_key')
    async def google_image(self, ctx:utils.Context, *, query:str):
        """
        Search a query on Google Images.
        """

        def formatter(menu, data):
            return utils.Embed(
                use_random_colour=True,
                title=data[0][0]
            ).set_image(
                data[0][1]
            ).set_footer(
                f"Page {menu.current_page + 1}"
            )
        await utils.Paginator(self.get_search_page(query, 1, True), formatter=formatter).start(ctx)


def setup(bot:utils.Bot):
    x = GoogleCommands(bot)
    bot.add_cog(x)
