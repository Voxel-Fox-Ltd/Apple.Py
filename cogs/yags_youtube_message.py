import discord
import voxelbotutils as utils


class YagsYoutubeMessage(utils.Cog):

    GUILD_ID = 208895639164026880
    YAGS_USER_ID = 204255221017214977
    YOUTUBE_UPDATE_ROLE = 731597271690510346

    @utils.Cog.listener()
    async def on_message(self, message:discord.Message):
        """
        Send a message to people who subscribe via Upgrade.chat.
        """

        if message.guild is None or message.guild.id != self.GUILD_ID:
            return
        if message.author.id != self.YAGS_USER_ID:
            return
        if "uploaded a new youtube video" not in message.content:
            return
        role = message.guild.get_role(self.YOUTUBE_UPDATE_ROLE)
        mentionable = role.mentionable
        await role.edit(mentionable=True)
        m = await message.channel.send(f'{role.mention} ' + message.content)
        await message.delete()
        await m.publish()
        await role.edit(mentionable=mentionable)


def setup(bot:utils.Bot):
    x = YagsYoutubeMessage(bot)
    bot.add_cog(x)
