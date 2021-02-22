import discord
from discord.ext import commands
import voxelbotutils as utils


class MeowChat(utils.Cog):

    def __init__(self, bot:utils.Bot):
        super().__init__(bot)
        self.meow_chats = set()

    @utils.Cog.listener()
    async def on_message(self, message:discord.Message):
        await self.check_message(message)

    @utils.Cog.listener()
    async def on_message_edit(self, before:discord.Message, after:discord.Message):
        await self.check_message(after)

    async def check_message(self, message:discord.Message):
        """
        Handles deleting any messages that aren't meow-friendly.
        """

        if message.channel not in self.meow_chats:
            return
        if message.author.bot:
            return
        if message.author.id in self.bot.owner_ids:
            return
        content = message.content.lower()
        if any([
                "mew" in content,
                "meow" in content,
                "nya" in content,
                "uwu" in content,
                "owo" in content,
                "x3" in content,
                ":3" in content,
                ]):
            return
        try:
            await message.delete()
            return await message.channel.send(f"{message.author.mention}, your message needs to have a 'meow' in it to be valid :<", delete_after=3)
        except discord.HTTPException:
            pass

    @utils.group()
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(send_messages=True, manage_messages=True)
    async def meow(self, ctx:utils.Context):
        """
        The parent group for the meow chat commands.
        """

        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @meow.command(name="enable", aliases=["start", "on"])
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(send_messages=True, manage_messages=True)
    async def meow_enable(self, ctx:utils.Context):
        """
        Turn on meow chat for this channel.
        """

        self.meow_chats.add(ctx.channel)
        await ctx.send(f"Meow chat has been enabled for {ctx.channel.mention} owo")

    @meow.command(name="disable", aliases=["stop", "off"])
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(send_messages=True, manage_messages=True)
    async def meow_disable(self, ctx:utils.Context):
        """
        Turn off meow chat for this channel.
        """

        self.meow_chats.remove(ctx.channel)
        await ctx.send(f"Meow chat has been disabled for {ctx.channel.mention} :<")


def setup(bot:utils.Bot):
    x = MeowChat(bot)
    bot.add_cog(x)
