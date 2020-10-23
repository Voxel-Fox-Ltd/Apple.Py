import re as regex

import discord
from discord.ext import commands
import voxelbotutils as utils


class SteamCommand(utils.Cog):

    ALL_GAMES_URL = "https://api.steampowered.com/ISteamApps/GetAppList/v2/"
    GAME_DATA_URL = "https://store.steampowered.com/api/appdetails"
    GAME_URL_REGEX = regex.compile(r"https:\/\/store\.steampowered\.com\/app\/(\d+)")
    headers = {
        "User-Agent": "Apple.py/0.0.1 - Discord@Caleb#2831"
    }

    def __init__(self, bot:utils.Bot):
        super().__init__(bot)
        self.game_cache: dict = None
        self.sent_message_cache = {}  # MessageID: {embed: Embed, index: ScreenshotIndex, screenshots: List[str]}

    async def load_game_cache(self):
        """Loads the games from Steam into cache"""

        params = {
            "key": self.bot.config['api_keys']['steam']
        }
        async with self.bot.session.get(self.ALL_GAMES_URL, params=params, headers=self.headers) as r:
            data = await r.json()
        apps = data['applist']['apps']
        self.game_cache = apps

    def get_valid_name(self, name):
        return ''.join(i for i in name if i.isdigit() or i.isalpha() or i.isspace())

    @utils.command(aliases=['steam'])
    async def steamsearch(self, ctx:utils.Context, *, app_name:str):
        """Search Steam for an item"""

        # Load cache
        if self.game_cache is None:
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
                app_object = [i for i in self.game_cache if i['appid'] == int(app_name)][0]
            except IndexError:
                pass

        # By app name
        if app_object is None and appid is None:
            app_name = self.get_valid_name(app_name)
            valid_items = [i for i in self.game_cache if app_name.lower() in self.get_valid_name(i['name']).lower()]
            full_title_match = [i for i in valid_items if app_name.lower() == self.get_valid_name(i['name']).lower()]
            if full_title_match:
                valid_items = [full_title_match[0]]
            if len(valid_items) > 1:
                return await ctx.send("There are multiple results with that name.")  # TODO
            elif len(valid_items) == 0:
                return await ctx.send("There are no results with that name.")  # TODO
            app_object = valid_items[0]
            appid = app_object['appid']

        # Get info
        params = {
            "appids": appid
        }
        async with self.bot.session.get(self.GAME_DATA_URL, params=params, headers=self.headers) as r:
            game_data = await r.json()
        if game_data[str(appid)]['success'] is False:
            return await ctx.send(f"I couldn't find an application with ID `{appid}`.")
        game_object = game_data[str(appid)]['data']

        # See if it's NSFW
        if int(game_object.get('required_age', '0')) >= 18 and ctx.channel.nsfw is False:
            return await ctx.send("That game is marked as an 18+, so can't be sent in a non-NSFW channel.")

        # Embed it babey
        with utils.Embed(use_random_colour=True) as embed:
            embed.title = game_object['name']
            embed.set_footer(text=f"AppID: {appid}")
            embed.description = game_object['short_description']
            embed.add_field("Developer", ', '.join(game_object['developers']), inline=True)
            embed.add_field("Publisher", ', '.join(game_object['publishers']), inline=True)
            embed.add_field("Genre", ', '.join(i['description'] for i in game_object['genres']), inline=True)
            if game_object.get('price_overview') is not None:
                initial_price = game_object['price_overview']['initial_formatted']
                final_price = game_object['price_overview']['final_formatted']
                embed.add_field("Price", f"~~{initial_price}~~ {final_price}" if initial_price else final_price, inline=True)
            embed.add_field("Link", f"Open with Steam - steam://store/{appid}\nOpen in browser - [Link](https://store.steampowered.com/app/{appid}/)", inline=False)
            screenshots = [i['path_full'] for i in game_object['screenshots']]
            embed.set_image(url=screenshots[0])

        # Send
        m = await ctx.send(embed=embed)
        self.sent_message_cache[m.id] = {
            "embed": embed,
            "screenshots": screenshots,
            "index": 0,
            "allowed_members": [ctx.author.id],
        }
        await m.add_reaction("⬅️")
        await m.add_reaction("➡️")

    @utils.Cog.listener()
    async def on_reaction_add(self, reaction:discord.Reaction, user:discord.User):
        """Changes the screenshot on an embed"""

        # Filter babey
        message = reaction.message
        if message.id not in self.sent_message_cache:
            return
        if user.bot:
            return

        # Get changed data
        data = self.sent_message_cache[message.id]
        if user.id not in data['allowed_members']:
            return

        # Get valid reaction
        if str(reaction.emoji) == "➡️":
            index = data['index'] + 1
            if index >= len(data['screenshots']):
                index = 0
        elif str(reaction.emoji) == "⬅️":
            index = data['index'] - 1
            if index < 0:
                index = len(data['screenshots']) - 1
        else:
            return

        # Change embed
        embed = data['embed']
        embed.set_image(url=data['screenshots'][index])
        embed.use_random_colour()
        data['embed'] = embed
        data['index'] = index
        self.sent_message_cache[message.id] = data
        await reaction.message.edit(embed=embed)
        try:
            await reaction.message.remove_reaction(str(reaction.emoji), user)
        except discord.Forbidden:
            pass


def setup(bot:utils.Bot):
    x = SteamCommand(bot)
    bot.add_cog(x)
