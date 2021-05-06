from datetime import datetime as dt
import random
import string

import discord
from discord.ext import commands, tasks
import voxelbotutils as utils


def create_id(n:int=5):
    """
    Generates a generic 5 character-string to use as an ID.
    """

    return ''.join(random.choices(string.digits, k=n))


class ReminderCommands(utils.Cog):

    def __init__(self, bot):
        super().__init__(bot)
        self.reminder_finish_handler.start()

    def cog_unload(self):
        self.reminder_finish_handler.stop()

    @utils.group(aliases=["reminders"], invoke_without_command=True)
    @commands.bot_has_permissions(send_messages=True)
    async def reminder(self, ctx:utils.Context):
        """
        The parent group for the reminder commands.
        """

        if ctx.invoked_subcommand is not None:
            return
        return await ctx.send_help(ctx.command)

    @reminder.command(name="list")
    @commands.bot_has_permissions(send_messages=True)
    async def reminder_list(self, ctx:utils.Context):
        """
        Shows you your reminders.
        """

        # Get the guild ID
        try:
            guild_id = ctx.guild.id
        except AttributeError:
            guild_id = 0

        # Grab their remidners
        async with self.bot.database() as db:
            rows = await db("SELECT * FROM reminders WHERE user_id=$1 and guild_id=$2", ctx.author.id, guild_id)

        # Format an output string
        reminders = ""
        for reminder in rows:
            expiry = utils.TimeValue((reminder['timestamp'] - dt.utcnow()).total_seconds()).clean_spaced or 'now'
            reminders += f"\n`{reminder['reminder_id']}` - {reminder['message'][:70]} ({expiry})"
        message = f"Your reminders: {reminders}"

        # Send to the user
        await ctx.send(message or "You have no reminders.", allowed_mentions=discord.AllowedMentions.none())

    @reminder.command(name="set", aliases=['create'])
    @commands.bot_has_permissions(send_messages=True)
    async def reminder_set(self, ctx:utils.Context, time:utils.TimeValue, *, message:str):
        """
        Adds a reminder to your account.
        """

        # Grab the guild ID
        try:
            guild_id = ctx.guild.id
        except AttributeError:
            guild_id = 0

        # Get untaken id
        db = await self.bot.database.get_connection()
        while True:
            reminder_id = create_id()
            data = await db("SELECT * FROM reminders WHERE reminder_id=$1", reminder_id)
            if not data:
                break

        # Chuck the info in the database
        await db(
            """INSERT INTO reminders (reminder_id, guild_id, channel_id, timestamp, user_id, message) VALUES ($1, $2, $3, $4, $5, $6)""",
            reminder_id, guild_id, ctx.channel.id, dt.utcnow() + time.delta, ctx.author.id, message
        )
        await db.disconnect()

        # Let them know its been set
        await ctx.send(f"Reminder set for {time.clean_spaced}.")

    @tasks.loop(seconds=30)
    async def reminder_finish_handler(self):
        """
        Handles reminders expiring.
        """

        # Grab finished stuff from the database
        db = await self.bot.database.get_connection()
        rows = await db("SELECT * FROM reminders WHERE timestamp < TIMEZONE('UTC', NOW())")
        if not rows:
            await db.disconnect()
            return

        # Go through all finished reminders
        expired_reminders = []
        for reminder in rows:
            channel_id = reminder["channel_id"]
            user_id = reminder["user_id"]
            message = reminder["message"]
            reminder_id = reminder["reminder_id"]

            try:
                channel = self.bot.get_channel(channel_id) or await self.bot.fetch_channel(channel_id)
            except discord.HTTPException:
                pass
            sendable = {
                "content": f"<@{user_id}> reminder `{reminder_id}` triggered - {message}",
                "allowed_mentions": discord.AllowedMentions(users=[discord.Object(user_id)]),
            }
            try:
                await channel.send(**sendable)
            except discord.Forbidden:
                try:
                    user = self.bot.get_user(user_id) or await self.bot.fetch_user(user_id)
                    await user.send(**sendable)
                except discord.HTTPException:
                    pass
            except AttributeError:
                pass
            expired_reminders.append(reminder_id)

        # Delete expired reminders
        await db("DELETE FROM reminders WHERE reminder_id=ANY($1::TEXT[])", expired_reminders)
        await db.disconnect()


def setup(bot:utils.Bot):
    x = ReminderCommands(bot)
    bot.add_cog(x)
