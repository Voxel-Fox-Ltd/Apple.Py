import discord
from discord.ext import commands, vbu


class GoogleCommands(vbu.Cog):

    def get_search_page(self, query: str, num: int, image: bool = False):
        """
        Get a number of results from Google
        """

        async def wrapper(page_number: int):
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
                    (
                        f"[{d['displayLink']}]({d['link']}) - "
                        f"{d['snippet'].replace(ENDL, ' ')}"
                    )
                )
            url = "https://customsearch.googleapis.com/customsearch/v1"
            async with self.bot.session.get(url, params=params) as r:
                data = await r.json()
            ENDL = '\n'
            output_data = []
            for d in data.get('items', list()):
                output_data.append(formatter(d))
            if not output_data:
                raise StopAsyncIteration()
            return output_data

        return wrapper

    @commands.group(
        invoke_without_command=True,
        aliases=['search'],
        application_command_meta=commands.ApplicationCommandMeta(),
    )
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    @vbu.checks.is_config_set('api_keys', 'google', 'search_engine_id')
    @vbu.checks.is_config_set('api_keys', 'google', 'api_key')
    async def google(self, ctx: vbu.Context):
        """
        The parent group for the google commands.
        """

        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @google.command(
        name="search",
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="query",
                    description="The text that you want to search.",
                    type=discord.ApplicationCommandOptionType.string,
                ),
            ],
        ),
    )
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    @vbu.checks.is_config_set('api_keys', 'google', 'search_engine_id')
    @vbu.checks.is_config_set('api_keys', 'google', 'api_key')
    async def google_search(self, ctx: vbu.Context, *, query: str):
        """
        Search a query on Google.
        """

        if query.startswith("-"):
            raise vbu.errors.MissingRequiredArgumentString("query")

        def formatter(menu, data):
            embed = vbu.Embed(use_random_colour=True)
            for d in data:
                embed.add_field(*d, inline=False)
            embed.set_footer(f"Page {menu.current_page + 1}/{menu.max_pages}")
            return embed
        await vbu.Paginator(
            self.get_search_page(query, 3),
            formatter=formatter
        ).start(ctx)

    @google.command(
        name='images',
        aliases=['image', 'i'],
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="query",
                    description="The text that you want to search.",
                    type=discord.ApplicationCommandOptionType.string,
                ),
            ],
        ),
    )
    @commands.has_permissions(embed_links=True)
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    @vbu.checks.is_config_set('api_keys', 'google', 'search_engine_id')
    @vbu.checks.is_config_set('api_keys', 'google', 'api_key')
    async def google_image(self, ctx: vbu.Context, *, query: str):
        """
        Search a query on Google Images.
        """

        if query.startswith("-"):
            raise vbu.errors.MissingRequiredArgumentString("query")

        def formatter(menu, data):
            return vbu.Embed(
                use_random_colour=True,
                title=data[0][0]
            ).set_image(
                data[0][1]
            ).set_footer(
                f"Page {menu.current_page + 1}/{menu.max_pages}"
            )
        await vbu.Paginator(
            self.get_search_page(query, 1, True),
            formatter=formatter,
        ).start(ctx)


def setup(bot: vbu.Bot):
    x = GoogleCommands(bot)
    bot.add_cog(x)
