import re

import discord

from cogs import utils


class RainbowLineAutodelete(utils.Cog):

    spoiler_regex = re.compile(r"\|\|.*\|\|", re.MULTILINE)
    rainbow_line = None
    shut = None
    snall_shut = None
    footer_shut = None

    def get_rainbow_line(self):
        if self.rainbow_line:
            return self.rainbow_line
        with open('config/rainbow_line.gif', 'rb') as a:
            constant = a.read()
        self.rainbow_line = constant
        return constant

    def get_shut(self):
        if self.shut:
            return self.shut
        with open('config/shut.jpg', 'rb') as a:
            constant = a.read()
        self.shut = constant
        return constant

    def get_small_shut(self):
        if self.small_shut:
            return self.small_shut
        with open('config/small_shut.jpg', 'rb') as a:
            constant = a.read()
        self.small_shut = constant
        return constant

    def get_footer_shut(self):
        if self.footer_shut:
            return self.footer_shut
        with open('config/shut_shut.jpg', 'rb') as a:
            constant = a.read()
        self.footer_shut = constant
        return constant

    async def compare_content(self, message, message_content, comparison_content):
        """"""

        if message_content == comparison_content:
            try:
                await message.delete()
            except discord.HTTPException as e:
                self.logger.error(e)
            return True
        return False

    @utils.Cog.listener()
    async def on_message(self, message:discord.Message):
        """Looks for the rainbow lines in messages and automatically deletes them"""

        # Filter out stuff
        if message.guild is None:
            return
        if self.bot.guild_settings[message.guild.id]['rainbow_line_autodelete'] is False:
            return
        if message.channel.permissions_for(message.author).manage_messages:
            return
        if self.spoiler_regex.search(message.content):
            return await message.delete()
        if not message.attachments:
            return
        if len(message.attachments) > 1:
            return
        attachment = message.attachments[0]

        # Get data
        async with self.bot.session.get(attachment.url) as r:
            content = await r.read()

        # Compare stuff
        await self.compare_content(message, content, self.get_rainbow_line())
        await self.compare_content(message, content, self.get_shut())
        await self.compare_content(message, content, self.get_small_shut())
        await self.compare_content(message, content, self.get_footer_shut())


def setup(bot:utils.Bot):
    x = RainbowLineAutodelete(bot)
    bot.add_cog(x)
