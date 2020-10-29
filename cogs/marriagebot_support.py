import voxelbotutils as utils


class MarriageBotHelper(utils.Cog):

    SUPPORT_CHANNEL_ID = 689189589776203861
    FAQ_CHANNEL_ID = 689189625356746755
    FAQ_MESSAGE_ID = 729049343260229652
    DIALOGFLOW_URL = "https://dialogflow.clients6.google.com/v2/projects/voxel-fox/agent/sessions/b40c7c12-4b0f-41a5-2537-71d84e6489ee:detectIntent"
    DISOWN_USER_INTENT = "projects/voxel-fox/agent/intents/b9d0a9d5-acce-4f64-97c7-0e3c3e39fe22"

    @utils.Cog.listener()
    async def on_message(self, message:discord.Message):
        """
        Listens for people saying "adopt", "disown", "kid", or "children", and runs that through Dialogflow to see
        if we should spit out the useid embed.
        """

        # Make sure we have an API key
        if not self.bot.config.get('api_keys', {}).get('dialogflow'):
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
        headers = {
            "Authorization": f"Bearer {self.bot.config['api_keys']['dialogflow']}",
        }
        async with self.bot.session.post(self.DIALOGFLOW_URL, json=json, headers=headers) as r:
            if r.status != 200:
                return
            data = await r.json()

        # Make sure it's right
        if data['queryResult']['intent']['name'] != self.DISOWN_USER_INTENT:
            return

        # Spit out result
        faq_message = await self.bot.get_channel(self.FAQ_CHANNEL_ID).fetch_message(self.FAQ_MESSAGE_ID)
        return await message.channel.send(embed=faq_message.embeds[0])


def setup(bot:utils.Bot):
    x = MarriageBotHelper(bot)
    bot.add_cog(x)
