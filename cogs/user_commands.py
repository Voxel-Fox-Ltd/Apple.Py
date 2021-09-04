import typing
import string

import discord
from discord.ext import commands, vbu



class UserCommands(vbu.Cog):

    EIGHT_BALL_ANSWERS = (
        "It is certain.",
        "It is decidedly so.",
        "Without a doubt.",
        "Yes – definitely.",
        "You may rely on it.",
        "As I see it, yes.",
        "Most likely.",
        "Outlook good.",
        "Yes.",
        "Signs point to yes.",
        "Reply hazy, try again.",
        "Ask again later.",
        "Better not tell you now.",
        "Cannot predict now.",
        "Concentrate and ask again.",
        "Don't count on it.",
        "My reply is no.",
        "My sources say no.",
        "Outlook not so good.",
        "Very doubtful. ",
    )

    @commands.context_command(name="Get ship percentage")
    async def _context_menu_ship(self, ctx: vbu.SlashContext, user: discord.Member):
        command = self.ship
        await command.can_run(ctx)
        await ctx.invoke(command, user)

    @commands.command()
    @commands.bot_has_permissions(send_messages=True)
    async def ship(self, ctx: vbu.Context, user: discord.Member, user2: discord.Member = None):
        """
        Gives you a ship percentage between two users.
        """

        # Fix attrs
        if user2 is None:
            user, user2 = ctx.author, user

        # Add response for yourself
        if user == user2:
            return await ctx.send("-.-")

        # Get percentage
        async with vbu.Database() as db:
            rows = await db("SELECT * FROM ship_percentages WHERE user_id_1=ANY($1::BIGINT[]) AND user_id_2=ANY($1::BIGINT[])", [user.id, user2.id])
        if rows and rows[0]['percentage']:
            percentage = rows[0]['percentage'] / 100
        else:
            percentage = ((user.id + user2.id + 4500) % 10001) / 100
        return await ctx.send(f"{user.mention} \N{REVOLVING HEARTS} **{percentage:.2f}%** \N{REVOLVING HEARTS} {user2.mention}", allowed_mentions=discord.AllowedMentions(users=False))

    @commands.command(add_slash_command=False)
    @vbu.checks.is_bot_support()
    @commands.bot_has_permissions(add_reactions=True)
    async def addship(self, ctx: vbu.Context, user1: discord.Member, user2: discord.Member = None, percentage: float = 0):
        """
        Add a custom ship percentage.
        """

        user2 = user2 or ctx.author
        percentage = max([min([percentage * 100, 10_000]), -10_000])
        async with vbu.Database() as db:
            await db(
                """INSERT INTO ship_percentages (user_id_1, user_id_2, percentage) VALUES ($1, $2, $3)
                ON CONFLICT (user_id_1, user_id_2) DO UPDATE SET percentage=excluded.percentage""",
                *sorted([user1.id, user2.id]), percentage,
            )
        await ctx.okay()

    @commands.command(aliases=['8ball'])
    @commands.bot_has_permissions(send_messages=True)
    async def eightball(self, ctx: vbu.Context, *, message: str):
        """
        Gives you an 8ball answer.
        """

        index = sum([ord(i) for i in message.lower().strip(string.punctuation + string.whitespace)]) % len(self.EIGHT_BALL_ANSWERS)
        return await ctx.send(self.EIGHT_BALL_ANSWERS[index])


def setup(bot: vbu.Bot):
    x = UserCommands(bot)
    bot.add_cog(x)
