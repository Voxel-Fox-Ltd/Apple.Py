import asyncio
import re
from datetime import datetime as dt

import discord
from discord.ext import commands
import voxelbotutils as vbu


class MeowChat(vbu.Cog):

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

    def __init__(self, bot: vbu.Bot):
        super().__init__(bot)
        self.meow_chats = set()
        self.meow_disable_tasks = {}

    @vbu.Cog.listener()
    async def on_message(self, message: discord.Message):
        await self.check_message(message)

    @vbu.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        await self.check_message(after)

    async def check_message(self, message: discord.Message):
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
            expiry_time, _ = self.meow_disable_tasks.get(ctx.channel.id, (None, None))
            if message.author.permissions_in(message.channel).manage_messages:
                text = f"{message.author.mention}, your message needs to have a 'meow' in it to be valid (to disable, run the `meow off` command)."
            else:
                text = f"{message.author.mention}, your message needs to have a 'meow' in it to be valid :<"
            if expiry_time:
                text = text.replace("in it", f"in it for {vbu.TimeFormatter(expiry_time).relative_time} more")
            await message.channel.send(text, delete_after=3)
        except discord.HTTPException:
            pass

    @vbu.group()
    @commands.has_permissions(manage_messages=True)
    @vbu.bot_has_permissions(send_messages=True, manage_messages=True)
    async def meow(self, ctx: vbu.Context):
        """
        The parent group for the meow chat commands.
        """

        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @meow.command(name="enable", aliases=["start", "on"])
    @commands.has_permissions(manage_messages=True)
    @vbu.bot_has_permissions(send_messages=True, manage_messages=True)
    async def meow_enable(self, ctx: vbu.Context, duration: vbu.TimeValue = None):
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
                    self.meow_chats.remove(ctx.channel)
                    await ctx.send("Turned off meow chat as scheduled :<")
                except KeyError:
                    pass
            _, current_task = self.meow_disable_tasks.get(ctx.channel.id, (None, None))
            if current_task:
                current_task.cancel()
            self.meow_disable_tasks[ctx.channel.id] = (dt.utcnow() + duration.delta, self.bot.loop.create_task(waiter()))

    @meow.command(name="disable", aliases=["stop", "off"])
    @commands.has_permissions(manage_messages=True)
    @vbu.bot_has_permissions(send_messages=True, manage_messages=True)
    async def meow_disable(self, ctx: vbu.Context):
        """
        Turn off meow chat for this channel.
        """

        try:
            self.meow_chats.remove(ctx.channel)
        except KeyError:
            return await ctx.send("Meow chat is already disabled in this channel.")
        await ctx.send(f"Meow chat has been disabled in {ctx.channel.mention} :<")

        # See if there's a running task to keep it alive
        expiry_time, current_task = self.meow_disable_tasks.pop(ctx.channel.id, (None, None))
        if current_task:
            current_task.cancel()


def setup(bot: vbu.Bot):
    x = MeowChat(bot)
    bot.add_cog(x)
