import asyncio
import random

from discord.ext import commands
import voxelbotutils as utils


class ThisOrThat(utils.Cog):

    THIS_OR_THAT_IDS = (
        199136310416375808,  # Apy
        619666943103729715,  # BigBen
        647301314732097560,  # Cerberus
        604059714963243056,  # Confessional
        731736201400418314,  # Flower
        690477072270753792,  # Honey
        598553427592871956,  # Profile
        760903667246432257,  # SimpTracker
    )

    @utils.command(hidden=True, aliases=['tot'])
    @commands.bot_has_permissions(send_messages=True, add_reactions=True)
    async def thisorthat(self, ctx:utils.Context):
        """
        Shows you two VFL bots. Asks which you prefer.
        """

        # Get two unique choices
        choice_one, choice_two = random.choices(self.THIS_OR_THAT_IDS, k=2)
        while choice_one == choice_two:
            choice_two = random.choice(self.THIS_OR_THAT_IDS)
        choice_one, choice_two = sorted([choice_one, choice_two])

        # Ask which they want
        ask_message = await ctx.send((
            f"Which bot do you prefer?\n"
            f"1\N{COMBINING ENCLOSING KEYCAP} <@{choice_one}>\n"
            f"2\N{COMBINING ENCLOSING KEYCAP} <@{choice_two}>\n"
        ))
        await ask_message.add_reaction("1\N{COMBINING ENCLOSING KEYCAP}")
        await ask_message.add_reaction("2\N{COMBINING ENCLOSING KEYCAP}")

        # Wait for response
        try:
            check = lambda r, u: str(r.emoji) in ["1\N{COMBINING ENCLOSING KEYCAP}", "2\N{COMBINING ENCLOSING KEYCAP}"] and u.id == ctx.author.id and r.message.id == ask_message.id
            reaction, _ = await self.bot.wait_for("reaction_add", check=check, timeout=15)
        except asyncio.TimeoutError:
            try:
                await ask_message.delete()
            except discord.HTTPException:
                pass
            return

        # Save response to database
        choice = {
            "1\N{COMBINING ENCLOSING KEYCAP}": choice_one,
            "2\N{COMBINING ENCLOSING KEYCAP}": choice_two,
        }[str(reaction.emoji)]
        self.logger.info("Saving thisorthat reaction to database")
        async with self.bot.database() as db:
            await db(
                """INSERT INTO this_or_that (compare_1, compare_2, choice, user_id) VALUES ($1, $2, $3, $4)
                ON CONFLICT (compare_1, compare_2, user_id) DO UPDATE SET choice=excluded.choice""",
                choice_one, choice_two, choice, ctx.author.id
            )

        # Edit message
        self.logger.info("Editing thisorthat message")
        try:
            await ask_message.edit(content=f"{ctx.author.mention} has voted that they prefer <@{choice}>! Run `{ctx.clean_prefix}thisorthat` yourself to vote.")
        except discord.HTTPException:
            pass


def setup(bot:utils.Bot):
    x = ThisOrThat(bot)
    bot.add_cog(x)
