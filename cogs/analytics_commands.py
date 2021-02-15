import discord
from discord.ext import commands
import voxelbotutils as utils


class AnalyticsCommands(utils.Cog):
    pass


def setup(bot:utils.Bot):
    x = AnalyticsCommands(bot)
    bot.add_cog(x)