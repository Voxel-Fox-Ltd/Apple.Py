import typing

import discord
from discord.ext import commands

from cogs import utils


class UserInfo(utils.Cog):

    @commands.command(cls=utils.Command)
    async def avatar(self, ctx:utils.Context, user:discord.User=None):
        """Shows you the avatar of a given user"""

        if user is None:
            user = ctx.author
        with utils.Embed(use_random_colour=True) as embed:
            embed.set_image(url=user.avatar_url)
        await ctx.send(embed=embed)


def setup(bot:utils.Bot):
    x = UserInfo(bot)
    bot.add_cog(x)
