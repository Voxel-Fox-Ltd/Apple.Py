import discord
from discord.ext import commands
import voxelbotutils as utils
from datetime import datetime as dt

def create_id(n: int=5):
    """
    Generates a generic 5 character-string to use as an ID.
    """

    return ''.join(random.choices(string.digits, k=n))


class ReminderCommands(utils.Cog):
	
	@utils.command(aliases=['reminder'])
	async def remindme(self, ctx: utils.Context, time: utils.TimeValue, message: commands.clean_content):

		# Grab guild id if ran in DMs set it as 0
		try:
		  	guild_id = ctx.guild.id
		except AttributeError:
		  	guild_id = 0

		timestamp = dt.utcnow() + time.delta

		await ctx.send(f"Reminder set in {time.clean_spaced}")

		# Get untaken id
		db = await self.bot.database.get_connection()
		for _ in range(4):
			reminder_id = create_id()
			data = await db("SELECT * FROM reminders WHERE guild_id = $1 and reminder_id = $2", guild_id, reminder_id)
			if len(data) == 0:
				break
			continue

		await db("INSERT INTO reminders (reminder_id, guild_id, channel_id, remind_at, user_id, message) VALUES ($1, $2, $3, $4, $5, $6, $7)",
			reminder_id, guild_id, ctx.channel.id, timestamp, ctx.author.id, message)
		await db.disconnect()



def setup(bot:utils.Bot):
    x = ReminderCommands(bot)
    bot.add_cog(x)
