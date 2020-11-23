from datetime import datetime as dt, timedelta

import discord
import voxelbotutils as utils


class MarriageBotHelper(utils.Cog):

    SUPPORT_CHANNEL_ID = 689189589776203861
    FAQ_CHANNEL_ID = 689189625356746755
    FAQ_MESSAGE_ID = 729049343260229652
    DIALOGFLOW_URL = "https://dialogflow.clients6.google.com/v2/projects/voxel-fox/agent/sessions/b40c7c12-4b0f-41a5-2537-71d84e6489ee:detectIntent"
    DISOWN_USER_INTENT = "projects/voxel-fox/agent/intents/b9d0a9d5-acce-4f64-97c7-0e3c3e39fe22"

    def __init__(self, bot:utils.Bot):
        super().__init__(bot)
        self.api_key = None

    async def get_access_token(self):
        """
        Get the Dialogflow access token for the bot
        """

        # See if we have an existing valid token
        if self.api_key is not None and self.api_key[1] < dt.utcnow() - timedelta(minutes=1):
            return self.api_key[0]

        # Alright sick let's get a new one
        json = self.bot.config.get('api_keys', {}).get('dialogflow', {})
        json.update({"grant_type": "refresh_token"})
        async with self.bot.session.post("https://oauth2.googleapis.com/token", json=json) as r:
            data = await r.json()
        self.logger.info(f"Asked for access token, got back {data}")
        self.api_key = (data['access_token'], dt.utcnow() + timedelta(seconds=data['expires_in']))
        return self.api_key[0]

    @utils.Cog.listener()
    async def on_message(self, message:discord.Message):
        """
        Listens for people saying "adopt", "disown", "kid", or "children", and runs that through Dialogflow to see
        if we should spit out the useid embed.
        """

        # Make sure we have an API key
        if not self.bot.config.get('api_keys', {}).get('dialogflow', {}):
            return

        # Make sure it's in the right place
        if message.author.bot:
            return
        if message.channel.id != self.SUPPORT_CHANNEL_ID:
            return

        # Make sure they said something fairly relevant
        if not any([
                "adopt" in message.content,
                "disown" in message.content,
                "kid" in message.content,
                "children" in message.content]):
            return

        # Make request
        json = {
            "queryInput": {
                "text": {
                    "text": message.content,
                    "languageCode": "en",
                },
            },
        }
        access_token = await self.get_access_token()
        headers = {
            "Authorization": f"Bearer {access_token}",
        }
        async with self.bot.session.post(self.DIALOGFLOW_URL, json=json, headers=headers) as r:
            if r.status != 200:
                return
            data = await r.json()
            self.logger.info(f"Asked for dialogflow information, got back {data}")

        # Make sure it's right
        if data['queryResult']['intent']['name'] != self.DISOWN_USER_INTENT:
            return

        # Spit out result
        faq_message = await self.bot.get_channel(self.FAQ_CHANNEL_ID).fetch_message(self.FAQ_MESSAGE_ID)
        return await message.channel.send(embed=faq_message.embeds[0])


def setup(bot:utils.Bot):
    x = MarriageBotHelper(bot)
    bot.add_cog(x)
