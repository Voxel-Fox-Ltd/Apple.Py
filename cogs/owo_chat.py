import asyncio
import re

import discord
from discord.ext import commands
import voxelbotutils as utils


class OwoChat(utils.Cog):

    VALID_KEYWORDS = (
        "owo",
        "uwu",
    )
    EMOJI_REGEX = re.compile(r"<a?:.+?:\d+?>")
   
    def __init__(self, bot:utils.Bot):
        super().__init__(bot)
        self.owo_chats = set()
        self.owo_disable_tasks = {}

    @utils.Cog.listener()
    async def on_message(self, message:discord.Message):
        await self.check_message(message)

    @utils.Cog.listener()
    async def on_message_edit(self, before:discord.Message, after:discord.Message):
        await self.check_message(after)

    async def check_message(self, message:discord.Message):
        """
        Handles doubling the slowmode time if owo is found :eyes:
        """

        if message.channel not in self.owo_chats:
            return
        if message.author.bot:
            return
        if message.author.id in self.bot.owner_ids or message.author.id == 322542134546661388 # georgie is safe :):
            return
        content = self.EMOJI_REGEX.sub("", message.content.lower())
        if any([i in content for i in self.VALID_KEYWORDS]):
            return
        try:
            await message.okay() # Reacts okay to the qualifying message. let the users know they fucked up
            current_delay = message.channel.slowmode_delay
            slowmode_time = (current_delay * 2) or 1 # The new slowmode_time is either double the first, or 1 if there is no current delay
            await message.channel.edit(slowmode_delay=slowmode_time)
        except discord.HTTPException:
            pass

    @utils.group()
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(send_messages=True, manage_messages=True)
    async def owo(self, ctx:utils.Context):
        """
        The parent group for the owo chat commands.
        """

        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @owo.command(name="enable", aliases=["start", "on"])
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(send_messages=True, manage_messages=True)
    async def owo_enable(self, ctx:utils.Context, duration:utils.TimeValue=None):
        """
        Turn on OwO chat for this channel.
        """

        self.owo_chats.add(ctx.channel)
        if duration:
            await ctx.send(f"OwO chat has been enabled in {ctx.channel.mention} for {duration.clean_full}")
        else:
            await ctx.send(f"OwO chat has been enabled in {ctx.channel.mention}")

        # See if we want to disable OwO chat after a while
        if duration:
            async def waiter():
                await asyncio.sleep(duration.delta.total_seconds())
                try:
                    self.owo_chats.remove(ctx.channel)
                    await ctx.send("Turned off OwO chat as scheduled :<")
                except KeyError:
                    pass
            current_task: asyncio.Task = self.owo_disable_tasks.get(ctx.channel.id)
            if current_task:
                current_task.cancel()
            self.owo_disable_tasks[ctx.channel.id] = self.bot.loop.create_task(waiter())

    @owo.command(name="disable", aliases=["stop", "off"])
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(send_messages=True, manage_messages=True)
    async def owo_disable(self, ctx:utils.Context):
        """
        Turn off owo chat for this channel.
        """

        try:
            self.owo_chats.remove(ctx.channel)
        except KeyError:
            return await ctx.send("OwO chat is already disabled in this channel.")
        await ctx.send(f"OwO chat has been disabled in {ctx.channel.mention} :<")

        # See if there's a running task to keep it alive
        current_task: asyncio.Task = self.owo_disable_tasks.pop(ctx.channel.id, None)
        if current_task:
            current_task.cancel()


def setup(bot:utils.Bot):
    x = OwoChat(bot)
    bot.add_cog(x)
