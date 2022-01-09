import asyncio
import typing
from datetime import datetime as dt, timedelta

import discord
from discord.ext import commands, vbu
import pytz


class TimezoneInfo(vbu.Cog):

    @commands.group(
        aliases=['tz'],
        application_command_meta=commands.ApplicationCommandMeta(),
    )
    async def timezone(self, ctx: vbu.Context):
        """
        The parent group for timezone commands.
        """

        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @staticmethod
    def get_common_timezone(name) -> str:
        if len(name) <= 4:
            name = name.upper()
        else:
            name = name.title()
        common_timezones = {
            "PST": "US/Pacific",
            "MST": "US/Mountain",
            "CST": "US/Central",
            "EST": "US/Eastern",
        }
        if name in common_timezones:
            name = common_timezones[name]
        return name

    @timezone.command(
        name="set",
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="offset",
                    description="The timezone that you live in.",
                    type=discord.ApplicationCommandOptionType.string,
                    autocomplete=True,
                ),
            ],
        ),
    )
    async def timezone_set(self, ctx: vbu.Context, *, offset: str = None):
        """
        Sets and stores your UTC offset into the bot.
        """

        # Ask them the question
        if offset is None:
            ask_message = await ctx.send((
                f"Hey, {ctx.author.mention}, what timezone are you currently in? You can give its name (`EST`, `GMT`, etc) "
                "or you can give your continent and nearest large city (`Europe/Amsterdam`, `Australia/Sydney`, etc) - this is "
                "case sensitive."
            ))
            try:
                check = lambda m: m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
                response_message = await self.bot.wait_for("message", check=check, timeout=30)
                offset = response_message.content
            except asyncio.TimeoutError:
                return await ask_message.delete()

        # See if it's one of the more common ones that I know don't actually exist
        offset = self.get_common_timezone(offset)

        # Try and parse the timezone name
        try:
            zone = pytz.timezone(offset)
        except pytz.UnknownTimeZoneError:
            return await ctx.send(f"I can't work out what timezone you're referring to - please run this command again to try later, or go to the website (`{ctx.clean_prefix}info`) and I can work it out automatically.")

        # Store it in the database
        async with vbu.Database() as db:
            await db(
                """INSERT INTO user_settings (user_id, timezone_name) VALUES ($1, $2) ON CONFLICT (user_id)
                DO UPDATE SET timezone_name=excluded.timezone_name""",
                ctx.author.id, zone.zone,
            )
        await ctx.send(f"I think your current time is **{discord.utils.utcnow().astimezone(zone).strftime('%-I:%M %p')}** - I've stored this in the database.")

    @commands.context_command(name="Get user's timezone")
    async def _context_command_timezone_get(self, ctx: vbu.SlashContext, user: discord.Member):
        command = self.timezone_get
        await command.can_run(ctx)
        await ctx.invoke(command, user)

    @timezone.command(
        name="get",
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="target",
                    description="The user whose timezone you want to get.",
                    type=discord.ApplicationCommandOptionType.user,
                    required=False,
                ),
            ],
        ),
    )
    @commands.defer()
    async def timezone_get(self, ctx: vbu.Context, target: typing.Union[discord.Member, str] = None):
        """
        Get the current time for a given user.
        """

        # Check if they are a bot
        target = target or ctx.author
        target_is_timezone = False
        if isinstance(target, str):
            target_is_timezone = True
            target = self.get_common_timezone(target)
        if isinstance(target, discord.Member) and target.bot:
            return await ctx.send("I don't think bots have timezones...")

        # See if they've set a timezone
        if not target_is_timezone:
            async with vbu.Database() as db:
                rows = await db("SELECT timezone_name, timezone_offset FROM user_settings WHERE user_id=$1", target.id)
            if not rows or (rows[0]['timezone_name'] is None and rows[0]['timezone_offset'] is None):
                return await ctx.send(f"{target.mention} hasn't set up their timezone information! They can set it by running `{ctx.clean_prefix}timezone set`.")

        # Grab their current time and output
        if target_is_timezone:
            try:
                formatted_time = (discord.utils.utcnow().astimezone(pytz.timezone(target))).strftime('%-I:%M %p')
            except pytz.UnknownTimeZoneError:
                return await ctx.send("That isn't a valid timezone.")
            return await ctx.send(f"The current time in **{target}** is estimated to be **{formatted_time}**.")
        elif rows:
            if rows[0]['timezone_name']:
                formatted_time = (discord.utils.utcnow().astimezone(pytz.timezone(rows[0]['timezone_name']))).strftime('%-I:%M %p')
            else:
                formatted_time = (discord.utils.utcnow() + timedelta(minutes=rows[0]['timezone_offset'])).strftime('%-I:%M %p')
            await ctx.send(f"The current time for {target.mention} is estimated to be **{formatted_time}**.", allowed_mentions=discord.AllowedMentions.none())


def setup(bot: vbu.Bot):
    x = TimezoneInfo(bot)
    bot.add_cog(x)
