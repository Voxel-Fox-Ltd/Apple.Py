import discord
from discord.ext import commands
import voxelbotutils as utils


class UserCommands(utils.Cog):

    @utils.command()
    async def ship(self, ctx:utils.Context, user:discord.Member, user2:discord.Member=None):
        """Gives you a ship percentage between two users"""

        # Fix attrs
        if user2 is None:
            user, user2 = ctx.author, user

        # Add response for yourself
        if user == user2:
            return await ctx.send("-.-")

        # Get percentage
        percentage = ((user.id + user2.id + 4500) % 10001) / 100
        return await ctx.send(f"{user.mention} \N{REVOLVING HEARTS} **{percentage:.2f}%** \N{REVOLVING HEARTS} {user2.mention}", allowed_mentions=discord.AllowedMentions(users=False))


def setup(bot:utils.Bot):
    x = UserCommands(bot)
    bot.add_cog(x)
