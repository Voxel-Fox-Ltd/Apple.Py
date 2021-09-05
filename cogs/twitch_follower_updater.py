from datetime import datetime as dt
import collections

import discord
from discord.ext import tasks, vbu


class TwitchFollowerUpdater(vbu.Cog):

    TWITCH_OAUTH_URL = "https://id.twitch.tv/oauth2/authorize"  # Used to make the login url
    TWITCH_VALIDATE_URL = "https://id.twitch.tv/oauth2/validate"  # Used to check their auth token
    TWITCH_USER_FOLLOWS_URL = "https://api.twitch.tv/helix/users/follows"  # Used to get their followers
    TWITCH_PARAMS = {
        "client_id": "4el1x73cztf2iglqfq58lt5a6ivpgdc",
        "redirect_uri": "http://localhost:3000",
        "response_type": "token",
        "scope": "channel:read:subscriptions",
    }

    def __init__(self, bot: vbu.Bot):
        super().__init__(bot)
        self.last_twitch_checked = discord.utils.utcnow()
        if bot.database.enabled:
            self.twitch_follower_checker_loop.start()

    def cog_unload(self):
        self.twitch_follower_checker_loop.cancel()

    @tasks.loop(minutes=5)
    async def twitch_follower_checker_loop(self):
        """
        Loop and check for new followers for given people on Twitch.
        """

        new_last_timestamp = discord.utils.utcnow()
        new_followers = collections.defaultdict(list)  # channel user id: list of new follower usernames
        db = await vbu.Database.get_connection()
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
            filtered_new_follower_list = [
                i for i in new_follower_list
                if dt.strptime(i['followed_at'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=new_last_timestamp.tzinfo) > self.last_twitch_checked
            ]

            # Send DM to the user
            if filtered_new_follower_list:
                discord_user = self.bot.get_user(row['user_id']) or await self.bot.fetch_user(row['user_id'])
                new_follower_string = ', '.join([f"**{i['from_name']}**" for i in filtered_new_follower_list])
                if len(new_follower_string) >= 1800:
                    new_follower_string = ""
                try:
                    await discord_user.send((
                        f"You have **{len(filtered_new_follower_list)}** new Twitch "
                        f"follower{'s' if len(filtered_new_follower_list) > 1 else ''}! "
                        f"{new_follower_string}"
                    ))
                except discord.HTTPException:
                    pass

        # Update timestamp
        self.last_twitch_checked = new_last_timestamp
        await db.disconnect()

    async def get_new_followers(self, bearer_token: str, user_id: str, after: str) -> tuple:
        """
        Gives you a list of new followers from after a given datetime.
        """

        headers = {
            "Client-Id": self.TWITCH_PARAMS['client_id'],
            "Authorization": f"Bearer {bearer_token}",
            "User-Agent": self.bot.user_agent,
        }
        params = {"to_id": user_id, "first": 100}
        if after:
            params["after"] = after
        output = []
        while True:
            async with self.bot.session.get(self.TWITCH_USER_FOLLOWS_URL, params=params, headers=headers) as r:
                data = await r.json()
            output.extend(data.get('data', list()))
            if len(data.get('data', list())) < 100:
                break
            params['after'] = data.get('pagination', {}).get('cursor', None)
        return output, data.get('pagination', {}).get('cursor', None)


def setup(bot: vbu.Bot):
    x = TwitchFollowerUpdater(bot)
    bot.add_cog(x)
