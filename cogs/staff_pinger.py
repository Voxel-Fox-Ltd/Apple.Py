import discord

from cogs import utils


class StaffPinger(utils.Cog):

    @utils.Cog.listener()
    async def on_message(self, message):
        if message.channel.id != 709608383216353280:
            return
        if message.author.id != 204255221017214977:
            return
        await message.delete()
        await message.channel.send(
            f"{message.content} <@&480519382699868181> <@&713026585569263637>",
            # allowed_mentions=discord.AllowedMentions(users=False)
        )


def setup(bot:utils.Bot):
    x = StaffPinger(bot)
    bot.add_cog(x)
