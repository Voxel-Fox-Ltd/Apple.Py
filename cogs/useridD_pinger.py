import re

import discord

from cogs import utils


class UserIDPinger(utils.Cog):

    GUILD_ID = 208895639164026880

    ID_IN_MESSAGE_MATCHER = re.compile(r"(?<!<@)[0-9]{15,23}(?!>)$")

    STAFF_COMMANDS_CHANNEL_ID = 528827626907762689

    @utils.Cog.listener()
    async def on_message(self, message:discord.Message):
        """Resends any message that countains a user ID sent in staff-commands with the mentioned user"""

        if message.guild is None or message.guild.id != self.GUILD_ID:
            return
        if message.channel.id != self.STAFF_COMMANDS_CHANNEL_ID:
            return

        # Regex Match
        m = self.ID_IN_MESSAGE_MATCHER.search(message.content)
        if m is None:
            return
        userid = m.group()

        # Send the ping-y boi
        try:
          await ctx.send(f"{self.bot.get_user(int(userid)).mention}")
        except AttributeError:
          return


def setup(bot:utils.Bot):
    x = UserIDPinger(bot)
    bot.add_cog(x)
