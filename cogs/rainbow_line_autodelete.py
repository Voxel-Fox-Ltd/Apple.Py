import discord
from discord.ext import commands

from cogs import utils


class RainbowLineAutodelete(utils.Cog):

    @utils.Cog.listener()
    async def on_message(self, message:discord.Message):
        """Looks for the rainbow lines in messages and automatically deletes them"""

        if message.guild is None:
            return
        if self.bot.guild_settings[message.guild.id]['rainbow_line_autodelete'] is False:
            return
        if message.channel.permissions_for(message.author).manage_messages:
            return
        if not message.attachments:
            return
        if len(message.attachments) > 1:
            return
        attachment = message.attachments[0]
        async with self.bot.session.get(attachment.url) as r:
            content = await r.read()
        with open('config/rainbow_line.gif', 'rb') as a:
            constant = a.read()
        if constant == content:
            try:
                await message.delete()
            except discord.HTTPException as e:
                self.logger.error(e)

def setup(bot:utils.Bot):
    x = RainbowLineAutodelete(bot)
    bot.add_cog(x)
