import re

import discord
from discord.ext import vbu


class UserIDPinger(vbu.Cog):

    GUILD_ID = 208895639164026880
    STAFF_CATEGORY_LIST = 512137728066977802
    ID_IN_MESSAGE_MATCHER = re.compile(r"(?<!<@)(?P<uid>[0-9]{15,23})(?!>)$")

    @vbu.Cog.listener()
    async def on_message(self, message: discord.Message):
        """
        Resends any message that countains a user ID sent in staff-commands with the mentioned user.
        """

        if message.guild is None or message.guild.id != self.GUILD_ID:
            return
        if message.channel.category_id != self.STAFF_CATEGORY_LIST:
            return

        # Regex Match
        m = self.ID_IN_MESSAGE_MATCHER.search(message.content)
        if m is None:
            return
        user_id = m.group("uid")

        # Send the pingy boi only if the user was found
        user = self.bot.get_user(int(user_id))
        if user:
            await message.channel.send(f"{user.mention}")
        

def setup(bot: vbu.Bot):
    x = UserIDPinger(bot)
    bot.add_cog(x)
