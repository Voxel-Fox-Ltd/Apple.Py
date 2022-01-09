from datetime import datetime as dt
import random
import string

import discord
from discord.ext import commands, tasks, vbu


def create_id(n: int = 5):
    """
    Generates a generic 5 character-string to use as an ID.
    """

    return ''.join(random.choices(string.digits, k=n))


class ReminderCommands(vbu.Cog):

    def __init__(self, bot):
        super().__init__(bot)
        if bot.database.enabled:
            self.reminder_finish_handler.start()

    def cog_unload(self):
        self.reminder_finish_handler.stop()

    @commands.group(
        aliases=["reminders"],
        invoke_without_command=True,
        application_command_meta=commands.ApplicationCommandMeta(),
    )
    @commands.bot_has_permissions(send_messages=True)
    async def reminder(self, ctx: vbu.Context):
        """
        The parent group for the reminder commands.
        """

        if ctx.invoked_subcommand is not None:
            return
        return await ctx.send_help(ctx.command)

    @reminder.command(
        name="list",
        application_command_meta=commands.ApplicationCommandMeta(),
    )
    @commands.bot_has_permissions(send_messages=True)
    async def reminder_list(self, ctx: vbu.Context):
        """
        Shows you your reminders.
        """

        # Get the guild ID
        try:
            guild_id = ctx.guild.id
        except AttributeError:
            guild_id = 0

        # Grab their remidners
        async with vbu.Database() as db:
            rows = await db("SELECT * FROM reminders WHERE user_id=$1 and guild_id=$2", ctx.author.id, guild_id)

        # Format an output string
        reminders = ""
        for reminder in rows:
            expiry = discord.utils.format_dt(reminder['timestamp'])
            reminders += f"\n`{reminder['reminder_id']}` - {reminder['message'][:70]} ({expiry})"
        message = f"Your reminders: {reminders}"

        # Send to the user
        await ctx.send(message or "You have no reminders.", allowed_mentions=discord.AllowedMentions.none())

    @reminder.command(
        name="set",
        aliases=['create'],
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="time",
                    description="How far into the future you want to set the reminder.",
                    type=discord.ApplicationCommandOptionType.string,
                ),
                discord.ApplicationCommandOption(
                    name="message",
                    description="The message that you want to set.",
                    type=discord.ApplicationCommandOptionType.string,
                ),
            ],
        ),
    )
    @commands.bot_has_permissions(send_messages=True)
    async def reminder_set(self, ctx: vbu.Context, time: vbu.TimeValue, *, message: str):
        """
        Adds a reminder to your account.
        """

        # Grab the guild ID
        try:
            guild_id = ctx.guild.id
        except AttributeError:
            guild_id = 0

        # Get untaken id
        db = await vbu.Database.get_connection()
        while True:
            reminder_id = create_id()
            data = await db("SELECT * FROM reminders WHERE reminder_id=$1", reminder_id)
            if not data:
                break

        # Let them know its been set
        m = await ctx.send(f"Reminder set for {discord.utils.format_dt(discord.utils.utcnow() + time.delta)}.")

        # Chuck the info in the database
        await db(
            """INSERT INTO reminders (reminder_id, guild_id, channel_id, message_id,
            timestamp, user_id, message)
            VALUES ($1, $2, $3, $4, $5, $6, $7)""",
            reminder_id, guild_id, ctx.channel.id, m.id,
            (discord.utils.utcnow() + time.delta).replace(tzinfo=None), ctx.author.id, message,
        )
        await db.disconnect()

    @reminder.command(
        name="delete",
        aliases=['remove'],
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="reminder_id",
                    description="The ID of the reminder that you want to delete.",
                    type=discord.ApplicationCommandOptionType.string,
                ),
            ],
        ),
    )
    @commands.bot_has_permissions(send_messages=True)
    async def reminder_delete(self, ctx: vbu.Context, reminder_id: str):
        """
        Deletes a reminder from your account.
        """

        # Grab the guild ID
        try:
            guild_id = ctx.guild.id
        except AttributeError:
            guild_id = 0

        # Grab the reminder
        async with self.bot.database() as db:
            data = await db("SELECT * FROM reminders WHERE reminder_id=$1 and guild_id=$2", reminder_id, guild_id)

            # Check if it exists
            if not data:
                return await ctx.send("That reminder doesn't exist.")

            # Delete it
            await db("DELETE FROM reminders WHERE reminder_id=$1 and user_id=$2", reminder_id, ctx.author.id)

        # Send feedback saying it was deleted
        await ctx.send("Reminder deleted.")

    @tasks.loop(seconds=30)
    async def reminder_finish_handler(self):
        """
        Handles reminders expiring.
        """

        # Grab finished stuff from the database
        db = await vbu.Database.get_connection()
        rows = await db("SELECT * FROM reminders WHERE timestamp < TIMEZONE('UTC', NOW())")
        if not rows:
            await db.disconnect()
            return

        # Go through all finished reminders
        expired_reminders = []
        for reminder in rows:
            channel_id = reminder["channel_id"]
            user_id = reminder["user_id"]
            message_id = reminder["message_id"]
            message = reminder["message"]
            reminder_id = reminder["reminder_id"]

            try:
                channel = self.bot.get_channel(channel_id) or await self.bot.fetch_channel(channel_id)
            except discord.HTTPException:
                channel = None
            sendable = {
                "content": f"<@{user_id}> reminder `{reminder_id}` triggered - {message}",
                "allowed_mentions": discord.AllowedMentions(users=[discord.Object(user_id)]),
            }
            if message_id:
                sendable.update({
                    "reference": discord.MessageReference(message_id=message_id, channel_id=channel_id),
                    "mention_author": True,
                })
            try:
                assert channel is not None
                try:
                    await channel.send(**sendable)
                except Exception:
                    sendable.pop("reference")
                    await channel.send(**sendable)
            except (AssertionError, discord.Forbidden):
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


def setup(bot: vbu.Bot):
    x = ReminderCommands(bot)
    bot.add_cog(x)
