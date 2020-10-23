import asyncio
from urllib.parse import urlencode, urlparse
from datetime import datetime as dt
import collections

import discord
from discord.ext import commands, tasks
import voxelbotutils as utils


class TwitchFollowerUpdater(utils.Cog):

    TWITCH_OAUTH_URL = "https://id.twitch.tv/oauth2/authorize"  # Used to make the login url
    TWITCH_VALIDATE_URL = "https://id.twitch.tv/oauth2/validate"  # Used to check their auth token
    TWITCH_USER_FOLLOWS_URL = "https://api.twitch.tv/helix/users/follows"  # Used to get their followers
    TWITCH_PARAMS = {
        "client_id": "4el1x73cztf2iglqfq58lt5a6ivpgdc",
        "redirect_uri": "http://localhost:3000",
        "response_type": "token",
        "scope": "channel:read:subscriptions",
    }

    def __init__(self, bot:utils.Bot):
        super().__init__(bot)
        self.last_twitch_checked = dt.utcnow()
        self.twitch_follower_checker_loop.start()

    def cog_unload(self):
        self.twitch_follower_checker_loop.cancel()

    @tasks.loop(minutes=5)
    async def twitch_follower_checker_loop(self):
        """Loop and check for new followers for given people on Twitch"""

        new_last_timestamp = dt.utcnow()
        new_followers = collections.defaultdict(list)  # channel user id: list of new follower usernames
        db = await self.bot.database.get_connection()
        data = await db("SELECT * FROM user_settings WHERE twitch_bearer_token IS NOT NULL")

        # Wew let's do it
        for row in data:

            # See if we got their data already
            new_follower_list = new_followers.get(row['twitch_user_id'])
            if new_follower_list is None:
                new_follower_list, new_cursor_value = await self.get_new_followers(row['twitch_bearer_token'], row['twitch_user_id'], row['twitch_cursor'])
                if new_cursor_value:
                    await db("UPDATE user_settings SET twitch_cursor=$1 WHERE twitch_user_id=$2", new_cursor_value, row['twitch_user_id'])
            new_followers[row['twitch_user_id']] = new_follower_list

            # Update the follower timestamps into real timestamps
            self.logger.info(new_follower_list)
            filtered_new_follower_list = [i for i in new_follower_list if dt.strptime(i['followed_at'], "%Y-%m-%dT%H:%M:%SZ") > self.last_twitch_checked]
            self.logger.info(filtered_new_follower_list)

            # Send DM to the user
            if filtered_new_follower_list:
                discord_user = self.bot.get_user(row['user_id']) or await self.bot.fetch_user(row['user_id'])
                new_follower_string = ', '.join([f"**{i['from_name']}**" for i in filtered_new_follower_list])
                if len(new_follower_string) >= 1800:
                    new_follower_string = ""
                try:
                    await discord_user.send(f"You have **{len(filtered_new_follower_list)}** new Twitch follower{'s' if len(filtered_new_follower_list) > 1 else ''}! {new_follower_string}")
                except discord.HTTPException:
                    pass

        # Update timestamp
        self.last_twitch_checked = new_last_timestamp
        await db.disconnect()

    async def get_new_followers(self, bearer_token:str, user_id:str, after:str) -> list:
        """Gives you a list of new followers from after a given datetime"""

        headers = {"Client-Id": self.TWITCH_PARAMS['client_id'], "Authorization": f"Bearer {bearer_token}"}
        params = {"to_id": user_id, "first": 100}
        if after:
            params["after"] = after
        output = []
        while True:
            async with self.bot.session.get(self.TWITCH_USER_FOLLOWS_URL, params=params, headers=headers) as r:
                data = await r.json()
                self.logger.info(data)
            output.extend(data['data'])
            if len(data['data']) < 100:
                break
            params['after'] = data.get('pagination', {}).get('cursor', None)
        return output, data.get('pagination', {}).get('cursor', None)

    @utils.command()
    @commands.bot_has_permissions(send_messages=True)
    async def linktwitch(self, ctx:utils.Context):
        """lorem ipsum"""

        # Send initial DM
        try:
            await ctx.author.send(f"Go to this URL, log in, and then paste the URL you're directed to right here! It'll look something like `http://localhost:3000/#access_token=123456789abcde`.\n\n<{self.TWITCH_OAUTH_URL}?{urlencode(self.TWITCH_PARAMS)}>")
        except discord.HTTPException:
            return await ctx.send("I wasn't able to send you a DM! Please enable DMs from this server to proceed.")
        if ctx.guild:
            await ctx.send("Sent you a DM!")

        # Wait for them to respond
        try:
            response_message = await self.bot.wait_for("message", check=lambda m: m.author.id == ctx.author.id and m.guild is None, timeout=60 * 5)
        except asyncio.TimeoutError:
            try:
                await ctx.author.send("Timed out waiting for a response.")
            except discord.HTTPException:
                pass
            return

        # Parse that
        url_object = urlparse(response_message.content)
        fragment = url_object.fragment
        query_params = {i.split('=')[0]: i.split('=')[1] for i in fragment.split('&')}
        if 'access_token' not in query_params:
            return await ctx.author.send("You gave an invalid return URL.")

        # Validate that
        async with self.bot.session.get(self.TWITCH_VALIDATE_URL, headers={"Authorization": f"Bearer {query_params['access_token']}"}) as r:
            data = await r.json()
            if r.status != 200:
                return await ctx.author.send("I couldn't validate your login data.")

        # Store that
        async with self.bot.database() as db:
            await db(
                """INSERT INTO user_settings (user_id, twitch_user_id, twitch_username, twitch_bearer_token) VALUES ($1, $2, $3, $4)
                ON CONFLICT (user_id) DO UPDATE SET twitch_user_id=excluded.twitch_user_id, twitch_username=excluded.twitch_username,
                twitch_bearer_token=excluded.twitch_bearer_token""",
                ctx.author.id, data['user_id'], data['login'], query_params['access_token'],
            )

        # Sick
        return await ctx.author.send(f"Logged in successfully as **{data['login']}**! You will now receive DMs when you get new followers.")


def setup(bot:utils.Bot):
    x = TwitchFollowerUpdater(bot)
    bot.add_cog(x)
