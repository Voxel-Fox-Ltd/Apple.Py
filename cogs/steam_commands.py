import re

import discord
from discord.ext import commands, vbu


class SteamCommand(vbu.Cog):

    ALL_GAMES_URL = "https://api.steampowered.com/ISteamApps/GetAppList/v2/"
    GAME_DATA_URL = "https://store.steampowered.com/api/appdetails"
    GAME_URL_REGEX = re.compile(r"https:\/\/store\.steampowered\.com\/app\/(\d+)")

    def __init__(self, bot: vbu.Bot):
        super().__init__(bot)
        self.game_cache: dict = {}

    async def load_game_cache(self):
        """
        Loads the games from Steam into cache.
        """

        params = {
            "key": self.bot.config['api_keys']['steam']
        }
        headers = {
            "User-Agent": self.bot.user_agent
        }
        async with self.bot.session.get(self.ALL_GAMES_URL, params=params, headers=headers) as r:
            data = await r.json()
        apps = data['applist']['apps']
        self.game_cache = apps

    def get_valid_name(self, name):
        return ''.join(i for i in name if i.isdigit() or i.isalpha() or i.isspace())

    @commands.command(
        aliases=['steamsearch'],
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="app_name",
                    description="The name of the game that you want to search for.",
                    type=discord.ApplicationCommandOptionType.string,
                ),
            ],
        ),
    )
    @commands.defer()
    @vbu.checks.is_config_set('api_keys', 'steam')
    async def steam(self, ctx: vbu.Context, *, app_name: str):
        """
        Search Steam for an item.
        """

        # Load cache
        if not self.game_cache:
            await self.load_game_cache()

        # Get app
        app_object = None
        appid = None
        await ctx.trigger_typing()

        # By url
        match = self.GAME_URL_REGEX.search(app_name)
        if match is not None:
            app_name = match.group(1)

        # By app id
        if app_name.isdigit():
            appid = int(app_name)
            try:
                app_object = [
                    i
                    for i in self.game_cache
                    if i['appid'] == int(app_name)
                ][0]
            except IndexError:
                pass

        # By app name
        if app_object is None and appid is None:
            app_name = self.get_valid_name(app_name)
            valid_items = [
                i
                for i in self.game_cache
                if app_name.lower() in self.get_valid_name(i['name']).lower()
            ]
            full_title_match = [
                i
                for i in valid_items
                if app_name.lower() == self.get_valid_name(i['name']).lower()
            ]
            if full_title_match:
                valid_items = [full_title_match[0]]
            if len(valid_items) > 1:
                output_items = valid_items[:10]
                output_ids = [f"`{i['appid']}` - {i['name']}" for i in output_items]
                return await ctx.send(
                    "There are multiple results with that name:\n"
                    + "\n".join(output_ids)
                )
            elif len(valid_items) == 0:
                return await ctx.send("There are no results with that name.")
            app_object = valid_items[0]
            appid = app_object['appid']

        # Get info
        params = {
            "appids": appid
        }
        headers = {
            "User-Agent": self.bot.user_agent
        }
        resp = await self.bot.session.get(self.GAME_DATA_URL, params=params, headers=headers)
        game_data = await resp.json()
        if game_data[str(appid)]['success'] is False:
            return await ctx.send(f"I couldn't find an application with ID `{appid}`.")
        game_object = game_data[str(appid)]['data']

        # See if it's NSFW
        required_age = int(game_object.get('required_age', '0')) >= 18
        if required_age and ctx.channel.nsfw is False:
            return await ctx.send(
                "That game is marked as an 18+, so can't "
                "be sent in a non-NSFW channel."
            )

        # Embed it babey
        e = vbu.Embed(use_random_colour=True)
        e.title = game_object['name']
        e.set_footer(text=f"AppID: {appid}")
        e.description = game_object['short_description']
        e.add_field(
            "Developer",
            ', '.join(game_object.get('developers', list())) or 'None',
            inline=True
        )
        e.add_field(
            "Publisher",
            ', '.join(game_object.get('publishers', list())) or 'None',
            inline=True
        )
        e.add_field(
            "Genre",
            ', '.join(i['description'] for i in game_object['genres']) or 'None',
            inline=True
        )
        if game_object.get('price_overview') is not None:
            initial_price = game_object['price_overview']['initial_formatted']
            final_price = game_object['price_overview']['final_formatted']
            e.add_field(
                "Price",
                (
                    f"~~{initial_price}~~ {final_price}"
                    if initial_price
                    else final_price
                ),
                inline=True,
            )
        url = f"https://store.steampowered.com/app/{appid}/"
        e.add_field(
            "Link",
            (
                f"Open with Steam - steam://store/{appid}\n"
                f"Open in browser - [Link]({url})"
            ),
            inline=False,
        )
        screenshots = [i['path_full'] for i in game_object['screenshots']]
        e.set_image(url=screenshots[0])

        # Send
        await ctx.send(embeds=[e])


def setup(bot: vbu.Bot):
    x = SteamCommand(bot)
    bot.add_cog(x)
