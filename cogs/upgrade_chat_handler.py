import discord
from discord.ext import vbu


class UpgradeChatHandler(vbu.Cog):

    USER_ID = 543974987795791872
    PURCHASE_CHANNEL = 743346070368813106

    @vbu.Cog.listener()
    async def on_message(self, message: discord.Message):
        """
        Suppress the embeds on Upgrade.Chat messages.
        """

        # Check the message is valid
        if message.author.id == self.USER_ID and message.channel.id == self.PURCHASE_CHANNEL:
            pass
        else:
            return

        # Suppress the embed
        r = discord.http.Route(
            "PATCH", "/channels/{channel_id}/messages/{message_id}",
            channel_id=message.channel.id, message_id=message.id,
        )
        await self.bot.http.request(r, json={"flags": 1 << 2})


def setup(bot: vbu.Bot):
    x = UpgradeChatHandler(bot)
    bot.add_cog(x)
