import re
import asyncio
from datetime import datetime as dt

import voxelbotutils as utils


class TimezoneInfo(utils.Cog):

    @utils.group(aliases=['tz'], hidden=True)
    async def timezone(self, ctx:utils.Context):
        """
        The parent group for timezone commands.
        """

        pass

    @timezone.command(hidden=True)
    async def set(self, ctx:utils.Context, *, offset:str=None):
        """
        Sets and stores your UTC offset into the bot
        """

        # Ask them the question
        ask_message = await ctx.send(f"Hey, {ctx.author.mention}! What's your current time? Give it in the format `XX:YY AM`")
        try:
            response_message = await self.bot.wait_for("message", check=lambda m: m.author.id == ctx.author.id and m.channel.id == ctx.channel.id, timeout=30)
        except asyncio.TimeoutError:
            await ask_message.delete()

        # See if their answer makes sense
        match = re.search(r"(?P<hour>\d?\d)[:-]?(?P<minute>\d\d) ?(?P<daytime>(?:AM)|(?:PM))?", response_message.content, re.IGNORECASE)
        if not match:
            return await ctx.send("You didn't give your time in the format provided. Please run this command again later to try again.")
        hour = int(match.group("hour"))
        minute = int(match.group("minute"))
        daytime = (match.group("daytime") or "am").lower()
        if hour >= 24 or minute >= 60 or (daytime == 'am' and hour > 12):
            return await ctx.send("Hmmmmmmm that isn't a valid time. Try again later.")
        elif daytime == 'pm' and hour < 12:
            hour += 12

        # Okay sick let's try and work out how far off we are
        now = dt.utcnow()
        hour_offset = now.hour - hour
        minute_offset = 15 * round((now.minute - minute) / 15)
        # total_minute_offset = (hour_offset * 60) + minute_offset
        return await ctx.send(f"Oki so I reckon you're UTC{hour_offset:=+03d}:{minute_offset:=02d}")


def setup(bot:utils.Bot):
    x = TimezoneInfo(bot)
    bot.add_cog(x)
