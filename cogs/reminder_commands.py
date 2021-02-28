import discord
from discord.ext import commands
from discord.ext import tasks
import voxelbotutils as utils
from datetime import datetime as dt
import random, string

def create_id(n: int=5):
    """
    Generates a generic 5 character-string to use as an ID.
    """

    return ''.join(random.choices(string.digits, k=n))


class ReminderCommands(utils.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.reminder_finish_handler.start()

    def cog_unload(self):
        self.reminder_finish_handler.stop()
    
    @utils.command(aliases=['reminder'])
    async def remindme(self, ctx: utils.Context, time: utils.TimeValue, *, message: commands.clean_content):

        # Grab guild id if ran in DMs set it as 0
        try:
            guild_id = ctx.guild.id
        except AttributeError:
            guild_id = 0

        # Let them know its been set
        await ctx.send(f"Reminder set in {time.clean_spaced}({dt.utcnow() + time.delta})")

        # Get untaken id
        db = await self.bot.database.get_connection()
        for _ in range(4):
            reminder_id = create_id()
            data = await db("SELECT * FROM reminders WHERE guild_id = $1 and reminder_id = $2", guild_id, reminder_id)
            if not data:
                break
            continue

        # Chuck the info in the database
        await db("INSERT INTO reminders (reminder_id, guild_id, channel_id, remind_at, user_id, message) VALUES ($1, $2, $3, $4, $5, $6)",
            reminder_id, guild_id, ctx.channel.id, dt.utcnow() + time.delta, ctx.author.id, message)
        await db.disconnect()


    @tasks.loop(seconds=30)
    async def reminder_finish_handler(self):
        """
        Handles giveaways expiring.
        """

        # Grab finished stuff from the database
        db = await self.bot.database.get_connection()
        rows = await db("SELECT * FROM reminders WHERE remind_at < TIMEZONE('UTC', NOW())")
        if not rows:
            await db.disconnect()
            return

        # Go through all finished reminders
        for reminder in rows:
            channel_id = reminder["channel_id"]
            user_id = reminder["user_id"]
            message = reminder["message"]
            reminder_id = reminder["reminder_id"]

            channel = self.bot.get_channel(channel_id) or await self.bot.fetch_channel(channel_id)
            try:
                await channel.send(f"Yo <@{user_id}>, I got a reminder for you :) - {message}")
            except discord.Forbidden:
                await (self.bot.get_user(user_id) or await self.bot.fetch_user(user_id)).send(f"Yo <@{user_id}>, I got a reminder for you :) - {message}")

            # Delete the reminder as we don't need it anymore
            await db("DELETE FROM reminders WHERE reminder_id = $1 and guild_id = $2", reminder_id, reminder["guild_id"])

        await db.disconnect()


    @utils.command()
    async def reminders(self, ctx: utils.Context):

        try:
              guild_id = ctx.guild.id
        except AttributeError:
              guild_id = 0

        no_reminders = False
        async with self.bot.database() as db:
            rows = await db("SELECT * FROM reminders WHERE user_id = $1 and guild_id = $2", ctx.author.id, guild_id)
            if not rows:
                no_reminders = True

        if no_reminders:
            message = "You have no reminders."
        else:
            reminders = ""
            for reminder in rows:
                reminders += f"\n{reminder['reminder_id']} - {reminder['message']} ({reminder['remind_at']})"
            # reminders = '\n'.join(reminders)
            message = f"Your reminders: {reminders}"

        await ctx.send(message)


def setup(bot:utils.Bot):
    x = ReminderCommands(bot)
    bot.add_cog(x)

# bot.add_cog(ReminderCommands(bot))