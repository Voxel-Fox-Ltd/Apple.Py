from discord.ext import commands
import voxelbotutils as vbu


class LockComamnds(vbu.Cog):

    @vbu.command()
    @commands.has_permissions(manage_channels=True, manage_roles=True)
    @commands.bot_has_permissions(manage_channels=True, manage_roles=True)
    @commands.guild_only()
    async def lock(self, ctx: vbu.Context):
        """
        Removes the read messages permission for the current channel.
        """

        await ctx.channel.set_permissions(ctx.guild.me, read_messages=True)
        await ctx.channel.set_permissions(ctx.guild.default_role, read_messages=False)
        await ctx.send("Done.")

    @vbu.command()
    @commands.has_permissions(manage_channels=True, manage_roles=True)
    @commands.bot_has_permissions(manage_channels=True, manage_roles=True)
    @commands.guild_only()
    async def unlock(self, ctx: vbu.Context):
        """
        Resets the read messages permission for the current channel.
        """

        await ctx.channel.set_permissions(ctx.guild.default_role, read_messages=None)
        await ctx.send("Done.")


def setup(bot: vbu.Bot):
    x = LockComamnds(bot)
    bot.add_cog(x)
