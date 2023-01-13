from datetime import datetime as dt

import discord
from discord.ext import vbu, commands


class ThreadTools(vbu.Cog[vbu.Bot]):

    @commands.command(
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="time",
                    type=discord.ApplicationCommandOptionType.string,
                    description=(
                        "How long without a message should be waited before "
                        "archive."
                    ),
                )
            ],
        ),
    )
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def archivethread(
            self,
            ctx: commands.SlashContext,
            time: vbu.TimeValue):
        """
        Archive the current thread in a given amount of time without a response.
        """

        # Make sure we're in a thread
        if not isinstance(ctx.channel, discord.Thread):
            return await ctx.interaction.response.send_message(
                "This isn't a thread.",
                ephemeral=True,
            )

        # Save to the database
        rows: list[dict] = []
        async with vbu.Database() as db:
            rows = await db.call(
                """
                INSERT INTO
                    thread_archive
                    (
                        thread_id,
                        timestamp
                    )
                VALUES
                    ($1, $2)
                ON CONFLICT
                    (thread_id)
                DO UPDATE
                SET
                    timestamp = excluded.timestamp
                RETURNING
                    *
                """,
                ctx.channel.id,
                dt.utcnow() + time.delta,
            )

        # Respond
        relative = discord.utils.format_dt(rows[0]['timestamp'], 'R')
        return await ctx.interaction.response.send_message(
            f"If there are no more messages in this channel, the thread "
            f"will be archived {relative}."
        )

    @vbu.Cog.listener("on_message")
    async def thread_message_listener(self, message: discord.Message):
        """
        Listen for messages being created in threads we care about.
        """

        if message.author.bot:
            return
        if message.guild is None:
            return
        if not isinstance(message.channel, discord.Thread):
            return
        async with vbu.Database() as db:
            rows = await db.call(
                """
                DELETE FROM
                    thread_archive
                WHERE
                    thread_id = $1
                    AND timestamp < TIMEZONE('UTC', NOW())
                RETURNING
                    *
                """,
                message.channel.id,
            )
        if not rows:
            return
        try:
            await message.channel.send(
                "Automatically archiving thread due to inactivity.",
            )
            await message.channel.edit(archived=True)
        except discord.HTTPException:
            pass  # Oh well


def setup(bot: vbu.Bot):
    x = ThreadTools(bot)
    bot.add_cog(x)
