import typing
import random
from urllib.parse import urlencode
import io
import http
import asyncio
import collections

import discord
from discord.ext import commands, vbu
import unicodedata
from PIL import Image


class MiscCommands(vbu.Cog):

    def __init__(self, bot:vbu.Bot):
        super().__init__(bot)
        self.button_message_locks = collections.defaultdict(asyncio.Lock)

    @commands.group(aliases=['topics'], invoke_without_command=False)
    @commands.bot_has_permissions(send_messages=True)
    async def topic(self, ctx: vbu.Context):
        """
        The parent group for the topic commands.
        """

        async with vbu.Database() as db:
            rows = await db("SELECT * FROM topics ORDER BY RANDOM() LIMIT 1")
        if not rows:
            return await ctx.send("There aren't any topics set up in the database for this bot :<")
        return await ctx.send(rows[0]['topic'])

    @topic.command(name="get")
    @commands.bot_has_permissions(send_messages=True)
    async def topic_get(self, ctx: vbu.Context):
        """
        Gives you a conversation topic.
        """

        await self.topic(ctx)

    @topic.command(name="add")
    @vbu.checks.is_bot_support()
    @commands.bot_has_permissions(send_messages=True)
    async def topic_add(self, ctx: vbu.Context, *, topic: str):
        """
        Add a new topic to the database.
        """

        async with vbu.Database() as db:
            await db("INSERT INTO topics VALUES ($1)", topic)
        return await ctx.send("Added to database.")

    @commands.command()
    @commands.bot_has_permissions(send_messages=True)
    async def coinflip(self, ctx: vbu.Context):
        """
        Flips a coin.
        """

        coin = ["Heads", "Tails"]
        return await ctx.send(random.choice(coin))

    @commands.command(aliases=['http'])
    @commands.cooldown(1, 5, commands.BucketType.channel)
    async def httpcat(self, ctx: vbu.Context, errorcode: str):
        """
        Gives you a cat based on an HTTP error code.
        """

        standard_errorcodes = [error.value for error in http.HTTPStatus]

        if errorcode in ('random', 'rand', 'r'):
            errorcode = random.choice(standard_errorcodes)
        else:
            try:
                errorcode = int(errorcode)
            except ValueError:
                return ctx.channel.send('Converting to "int" failed for parameter "errorcode".')

        await ctx.trigger_typing()
        headers = {"User-Agent": self.bot.user_agent}
        async with self.bot.session.get(f"https://http.cat/{errorcode}", headers=headers) as r:
            if r.status == 404:
                if errorcode not in standard_errorcodes:
                    await ctx.send("That HTTP code doesn't exist.")
                else:
                    await ctx.send('Image for HTTP code not found on provider.')
                return
            if r.status != 200:
                await ctx.send(f'Something went wrong, try again later. ({r.status})')
                return
        with vbu.Embed(use_random_colour=True) as embed:
            embed.set_image(url=f'https://http.cat/{errorcode}')
        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.channel)
    async def httpdog(self, ctx: vbu.Context, errorcode: str):
        """
        Gives you a dog based on an HTTP error code.
        """

        standard_errorcodes = [error.value for error in http.HTTPStatus]

        if errorcode in ('random', 'rand', 'r'):
            errorcode = random.choice(standard_errorcodes)
        else:
            try:
                errorcode = int(errorcode)
            except ValueError:
                return ctx.channel.send('Converting to "int" failed for parameter "errorcode".')

        await ctx.trigger_typing()
        headers = {"User-Agent": self.bot.user_agent}
        async with self.bot.session.get(
                f"https://httpstatusdogs.com/img/{errorcode}.jpg", headers=headers, allow_redirects=False) as r:
            if str(r.status)[0] != "2":
                if errorcode not in standard_errorcodes:
                    await ctx.send("That HTTP code doesn't exist.")
                else:
                    await ctx.send('Image for HTTP code not found on provider.')
                return
        with vbu.Embed(use_random_colour=True) as embed:
            embed.set_image(url=f'https://httpstatusdogs.com/img/{errorcode}.jpg')
        await ctx.send(embed=embed, wait=False)

    @commands.command(aliases=['color'])
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def colour(self, ctx: vbu.Context, *, colour: typing.Union[vbu.converters.ColourConverter, discord.Role, discord.Member]):
        """
        Get you a colour.
        """

        # https://www.htmlcsscolor.com/preview/gallery/5dadec.png
        if isinstance(colour, discord.Role):
            colour = colour.colour
        elif isinstance(colour, discord.Member):
            try:
                colour = [i for i in colour.roles if i.colour.value > 0][-1].colour
            except IndexError:
                colour = discord.Colour(0)
        hex_colour = colour.value
        with vbu.Embed(colour=hex_colour,title=f"#{hex_colour:0>6X}") as embed:
            embed.set_image(url=f"https://www.htmlcsscolor.com/preview/gallery/{hex_colour:0>6X}.png")
        await ctx.send(embed=embed, wait=False)

    @commands.command(add_slash_command=False, cooldown_after_parsing=True)
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(send_messages=True)
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def spam(self, ctx: vbu.Context, amount: int, *, text: str):
        """
        Spams a message a given amount of times.
        """

        if amount > 10:
            return await ctx.send("That's too much to spam.")
        for _ in range(amount):
            await ctx.send(text)

    @commands.command(aliases=['disconnectvc', 'clearvc'])
    @commands.has_guild_permissions(move_members=True)
    @commands.bot_has_guild_permissions(move_members=True)
    @commands.bot_has_permissions(send_messages=True)
    async def emptyvc(self, ctx: vbu.Context, channel: discord.VoiceChannel):
        """
        Removes all the people from a given VC.
        """

        if not channel.members:
            return await ctx.send("There are no people in that VC for me to remove.")
        member_count = len(channel.members)
        await ctx.defer()
        for member in channel.members:
            try:
                await member.edit(voice_channel=None)
            except discord.Forbidden:
                return await ctx.send("I don't have permission to remove members from that channel.")
        return await ctx.send(f"Dropped {member_count} members from the VC.")

    @commands.command()
    @commands.bot_has_permissions(send_messages=True)
    async def buttons(self, ctx: vbu.Context):
        """
        Makes a cute lil message of clickable buttons.
        """

        def make_button(i):
            return discord.ui.Button("X", f"DISABLE_BUTTON_COMMAND {i}", style=discord.ui.ButtonStyle(random.randint(1, 4)))
        await ctx.send(
            "OwO button time",
            components=discord.ui.MessageComponents.add_buttons_with_rows(
                *[make_button(i) for i in range(25)]
            ),
        )

    @vbu.Cog.listener()
    async def on_button_click(self, payload):
        """
        Disables a given button.
        """

        if not payload.component.custom_id.startswith("DISABLE_BUTTON_COMMAND"):
            return
        async with self.button_message_locks[payload.message.id]:
            components = discord.ui.MessageComponents(*[
                discord.ui.ActionRow(*[
                    discord.ui.Button.from_dict(b) for b in r['components']
                ]) for r in payload.data['message']['components']
            ])
            b: discord.ui.Button = components.get_component(payload.component.custom_id)
            b.disabled = True
            await payload.ack()
            await payload.message.edit(components=components)


def setup(bot: vbu.Bot):
    x = MiscCommands(bot)
    bot.add_cog(x)
