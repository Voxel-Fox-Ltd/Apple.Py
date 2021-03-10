import asyncio
import re

import discord
from discord.ext import commands
import voxelbotutils as utils


class MeowChat(utils.Cog):

    VALID_KEYWORDS = (
        "mew",
        "meow",
        "nya",
        "uwu",
        "owo",
        "x3",
        ":3",
        ";3",
        "rawr",
        "purr",
        "murr",
        "nuzzle",
    )
    EMOJI_REGEX = re.compile(r"<a?:.+?:\d+?>")

    def __init__(self, bot:utils.Bot):
        super().__init__(bot)
        self.meow_chats = set()
        self.meow_disable_tasks = {}

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
        content = self.EMOJI_REGEX.sub("", message.content.lower())
        if any([i in content for i in self.VALID_KEYWORDS]):
            return
        try:
            await message.delete()
            if message.author.permissions_in(message.channel).manage_messages:
                await message.channel.send(f"{message.author.mention}, your message needs to have a 'meow' in it to be valid (to disable, run the `meow off` command).", delete_after=6)
            else:
                await message.channel.send(f"{message.author.mention}, your message needs to have a 'meow' in it to be valid :<", delete_after=3)
        except discord.HTTPException:
            pass

    @utils.group()
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(send_messages=True, manage_messages=True)
    async def meow(self, ctx:utils.Context):
        """
        The parent group for the meow chat commands.
        """

        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @meow.command(name="enable", aliases=["start", "on"])
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(send_messages=True, manage_messages=True)
    async def meow_enable(self, ctx:utils.Context, duration:utils.TimeValue=None):
        """
        Turn on meow chat for this channel.
        """

        self.meow_chats.add(ctx.channel)
        if duration:
            await ctx.send(f"Meow chat has been enabled in {ctx.channel.mention} for {duration.clean_full} owo")
        else:
            await ctx.send(f"Meow chat has been enabled in {ctx.channel.mention} owo")

        # See if we want to disable meow chat after a while
        if duration:
            async def waiter():
                await asyncio.sleep(duration.delta.total_seconds())
                try:
                    self.meow_chats.add(ctx.channel)
                    await ctx.send("Turned off meow chat as scheduled :<")
                except KeyError:
                    pass
            current_task: asyncio.Task = self.meow_disable_tasks.get(ctx.channel.id)
            if current_task:
                current_task.cancel()
            self.meow_disable_tasks[ctx.channel.id] = self.bot.loop.create_task(waiter())


    @meow.command(name="disable", aliases=["stop", "off"])
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(send_messages=True, manage_messages=True)
    async def meow_disable(self, ctx:utils.Context):
        """
        Turn off meow chat for this channel.
        """

        try:
            self.meow_chats.remove(ctx.channel)
        except KeyError:
            return await ctx.send("Meow chat is already disabled in this channel.")
        await ctx.send(f"Meow chat has been disabled in {ctx.channel.mention} :<")

        # See if there's a running task to keep it alive
        current_task: asyncio.Task = self.meow_disable_tasks.pop(ctx.channel.id, None)
        if current_task:
            current_task.cancel()


def setup(bot:utils.Bot):
    x = MeowChat(bot)
    bot.add_cog(x)
