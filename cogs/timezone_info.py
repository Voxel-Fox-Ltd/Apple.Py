import re
import asyncio
from datetime import datetime as dt, timedelta

import discord
import voxelbotutils as utils


class TimezoneInfo(utils.Cog):

    @utils.group(aliases=['tz'])
    async def timezone(self, ctx:utils.Context):
        """
        The parent group for timezone commands.
        """

        pass

    @timezone.command(name="set")
    async def timezone_set(self, ctx:utils.Context, *, offset:str=None):
        """
        Sets and stores your UTC offset into the bot
        """

        # Ask them the question
        if offset is None:
            ask_message = await ctx.send(f"Hey, {ctx.author.mention}! What's your current time? Give it in the format `XX:YY AM`")
            try:
                response_message = await self.bot.wait_for("message", check=lambda m: m.author.id == ctx.author.id and m.channel.id == ctx.channel.id, timeout=30)
                offset = response_message.content
            except asyncio.TimeoutError:
                await ask_message.delete()

        # See if their answer makes sense
        match = re.search(r"(?P<hour>\d?\d)[:-]?(?P<minute>\d\d) ?(?P<daytime>(?:AM)|(?:PM))?", offset, re.IGNORECASE)
        if not match:
            return await ctx.send("You didn't give your time in the format provided. Please run this command again later to try again.")
        hour = int(match.group("hour"))
        minute = int(match.group("minute"))
        daytime = (match.group("daytime") or "am").lower()
        if hour >= 24 or minute >= 60:  # or (daytime == 'am' and hour > 12):
            return await ctx.send("It looks like the time you provided isn't valid; please try again later.")
        elif daytime == 'pm' and hour < 12:
            hour += 12

        # Okay sick let's try and work out how far off we are
        now = dt.utcnow()
        hour_offset = hour - now.hour
        minute_offset = 15 * round((minute - now.minute) / 15)
        if minute_offset < 0:
            minute_offset += 60
            hour_offset -= 1
        if hour_offset > 12:
            hour_offset -= 24
        elif hour_offset < -12:
            hour_offset += 24
        total_minute_offset = (hour_offset * 60) + minute_offset

        # Store it in the database
        async with self.bot.database() as db:
            await db(
                """INSERT INTO user_settings (user_id, timezone_offset) VALUES ($1, $2) ON CONFLICT (user_id)
                DO UPDATE SET timezone_offset=excluded.timezone_offset""",
                ctx.author.id, total_minute_offset,
            )
        await ctx.send(f"I think you're somewhere around **UTC{hour_offset:=+03d}:{minute_offset:=02d}** - I've stored this in the database.")

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
        formatted_time = (dt.utcnow() + timedelta(minutes=rows[0]['timezone_offset'])).strftime('%-I:%M %p')
        await ctx.send(f"The current time for {user.mention} _should_ be somewhere around **{formatted_time}**.", allowed_mentions=discord.AllowedMentions.none())


def setup(bot:utils.Bot):
    x = TimezoneInfo(bot)
    bot.add_cog(x)
