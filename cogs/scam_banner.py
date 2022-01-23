import re

import discord
from discord.ext import vbu


SCAM_REGEX = re.compile(
    r"""
        (gift|nitro|airdrop|@everyone|:\))
        .+?
        (
            (https?://)(\S*?)
            (
                ((?:d|cl)s?[li](?:sc|cs|zc|cz|s|c|sck)r?oc?r?c?(?:d|cl)?s?)
                (\S*?)\.
                (com|pw|org|app|info|net|gift|codes|click|club)
            )
        )
    """,
    re.MULTILINE | re.DOTALL | re.VERBOSE | re.IGNORECASE,
)


class ScamBanner(vbu.Cog):

    @vbu.Cog.listener()
    async def on_message(self, message: discord.Message):

        # Ignore DMs
        if message.guild is None:
            return
        if message.guild.id != 208895639164026880:
            return

        # Ignore people with roles
        try:
            assert isinstance(message.author, discord.Member)
        except AssertionError:
            return  # They were already banned
        if len(message.author.roles) > 1:
            return

        # See if we match
        match = SCAM_REGEX.search(message.content)
        if not match:
            return
        
        matched_domain = match.group(5).lower()

        # Leave the legit links alone
        valid_links = [
            "discord.gift",
            "discordapp.com",
            "discord.com",
            "discord.gg",
        ]
        if matched_domain in valid_links:
            return

        # Ban the user
        try:
            await message.author.ban(reason=f"Suspected scam link ({matched_domain})")
        except discord.HTTPException:
            pass


def setup(bot: vbu.Bot):
    x = ScamBanner(bot)
    bot.add_cog(x)
