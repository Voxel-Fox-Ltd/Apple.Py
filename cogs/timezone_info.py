import asyncio
from datetime import datetime as dt, timedelta

import discord
import voxelbotutils as utils
import pytz


class TimezoneInfo(utils.Cog):

    @utils.group(aliases=['tz'])
    async def timezone(self, ctx:utils.Context):
        """
        The parent group for timezone commands.
        """

        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @timezone.command(name="set")
    async def timezone_set(self, ctx:utils.Context, *, offset:str=None):
        """
        Sets and stores your UTC offset into the bot.
        """

        # Ask them the question
        if offset is None:
            ask_message = await ctx.send((
                f"Hey, {ctx.author.mention}, what timezone are you currently in? You can give its name (`EST`, `GMT`, etc) "
                "or you can give your continent and nearest capital city (`Europe/Amsterdam`, `Australia/Sydney`, etc)."
            ))
            try:
                check = lambda m: m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
                response_message = await self.bot.wait_for("message", check=check, timeout=30)
                offset = response_message.content
            except asyncio.TimeoutError:
                await ask_message.delete()

        # Try and parse the timezone name
        try:
            zone = pytz.timezone(response_message.content)
        except pytz.UnknownTimeZoneError:
            return await ctx.send("I can't work out what timezone you're referring to - please run this command again to try later.")

        # Store it in the database
        async with self.bot.database() as db:
            await db(
                """INSERT INTO user_settings (user_id, timezone_name) VALUES ($1, $2) ON CONFLICT (user_id)
                DO UPDATE SET timezone_name=excluded.timezone_name""",
                ctx.author.id, zone.zone,
            )
        await ctx.send(f"I think your current time is **{dt.utcnow().astimezone(zone).strftime('%-I:%M %p')}** - I've stored this in the database.")

    @timezone.command(name="get")
    async def timezone_get(self, ctx:utils.Context, user:discord.Member=None):
        """
        Get the current time for a given user.
        """

        # Check if they are a bot
        user = user or ctx.author
        if user.bot:
            return await ctx.send("I don't think bots have timezones...")

        # Store it in the database
        async with self.bot.database() as db:
            rows = await db("SELECT timezone_offset FROM user_settings WHERE user_id=$1", user.id)
        if not rows or rows[0]['timezone_offset'] is None:
            return await ctx.send(f"{user.mention} hasn't set up their timezone information! They can set it with `{ctx.clean_prefix}timezone set`.")
        formatted_time = (dt.utcnow().astimezone(pytz.timezone(minutes=rows[0]['timezone_name']))).strftime('%-I:%M %p')
        await ctx.send(f"The current time for {user.mention} is estimated to be **{formatted_time}**.", allowed_mentions=discord.AllowedMentions.none())


def setup(bot:utils.Bot):
    x = TimezoneInfo(bot)
    bot.add_cog(x)
