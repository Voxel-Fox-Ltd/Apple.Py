import discord
from discord.ext import vbu


class YagsYoutubeMessage(vbu.Cog):

    STREAM_UPDATES_CHANNEL = 738061851014856774
    YAGS_USER_ID = 204255221017214977
    YOUTUBE_UPDATE_ROLE = 731597271690510346

    @vbu.Cog.listener()
    async def on_message(self, message: discord.Message):
        """
        Ping the updates role when Kae goes live on Twitch etc.
        """

        if message.channel.id != self.STREAM_UPDATES_CHANNEL or message.guild is None:
            return
        if message.author.id != self.YAGS_USER_ID:
            self.logger.info("Message in stream updates channel - not posted by Yags.")
            return
        if "**Kae** uploaded a new youtube video" not in message.content and "**Kae** is currently streaming" not in message.content:
            self.logger.info("Message in stream updates channel - not a notification.")
            return
        role = message.guild.get_role(self.YOUTUBE_UPDATE_ROLE)
        if role is None:
            self.logger.info("Message in stream updates channel - could not get role.")
            return
        mentionable = role.mentionable
        await role.edit(mentionable=True)
        m = await message.channel.send(f'{role.mention} {message.content}')
        await message.delete()
        await m.publish()
        await role.edit(mentionable=mentionable)
        self.logger.info("Sent new message in stream updates channel.")


def setup(bot: vbu.Bot):
    x = YagsYoutubeMessage(bot)
    bot.add_cog(x)
