import re

import discord
import voxelbotutils as utils


class DonatorMessage(utils.Cog):

    GUILD_ID = 208895639164026880

    UPGRADE_CHAT_MATCHER = re.compile(r"^<@!?(?P<userid>\d+)> just (purchased the role|Upgraded to) (?:\*\*)?(?P<rolename>.+)(?:\*\*)?(\.|!)$")

    UPGRADE_CHAT_USER_ID = 543974987795791872
    UPGRADE_CHAT_CHANNEL_ID = 743346070368813106
    BOT_COMMANDS_CHANNEL_ID = 490991441255071745

    @utils.Cog.listener()
    async def on_message(self, message:discord.Message):
        """Send a message to people who subscribe via Upgrade.chat"""

        if message.guild is None or message.guild.id != self.GUILD_ID:
            return
        if message.channel.id == self.UPGRADE_CHAT_CHANNEL_ID and message.author.id == self.UPGRADE_CHAT_USER_ID:
            pass
        else:
            return

        # Match the regex
        m = self.UPGRADE_CHAT_MATCHER.search(message.content)
        if m is None:
            return

        # See who bought what
        donator = self.bot.get_user(int(m.group("userid")))
        role = m.group("rolename")

        # Cheers donators but you already lost your money
        if role == 'Donator':
            return

        # And send them the message
        emoji = "\N{LOVE LETTER}"
        try:
            await donator.send(f"Thank you for purchasing **{role}**! Your MarriageBot perks will be applied automatically. As the perks are tied to the role you just purchased, your perks will be automatically removed should you leave the server. If at any point you want to stop supporting MarriageBot, you can run `$downgrade` in <#{self.BOT_COMMANDS_CHANNEL_ID}>.\nHave a nice day! :D")
        except (discord.Forbidden, AttributeError):
            emoji = "\N{HEAVY EXCLAMATION MARK SYMBOL}"
        await message.add_reaction(emoji)


def setup(bot:utils.Bot):
    x = DonatorMessage(bot)
    bot.add_cog(x)
