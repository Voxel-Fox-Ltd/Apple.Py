import typing

import discord
from discord.ext import commands

from cogs import utils


class UserInfo(utils.Cog):

    @commands.command(cls=utils.Command)
    async def avatar(self, ctx:utils.Context, user:typing.Optional[discord.User]=None):
        """Shows you the avatar of a given user"""

        if user is None:
            user = ctx.author
        colour = None
        if ctx.guild:
            colour = ctx.guild.get_member(user.id).top_role.colour
        with utils.Embed(colour=colour) as embed:
            embed.set_image(url=user.avatar_url)
        if colour is None:
            embed.use_random_colour()
        await ctx.send(embed=embed)


def setup(bot:utils.Bot):
    x = UserInfo(bot)
    bot.add_cog(x)
