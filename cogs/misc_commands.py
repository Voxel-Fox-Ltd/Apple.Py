import typing
import random
from urllib.parse import urlencode
import io
import http

import discord
from discord.ext import commands
import unicodedata
from PIL import Image
import voxelbotutils as utils


class MiscCommands(utils.Cog):

    @utils.group(aliases=['topics'], invoke_without_command=False)
    @commands.bot_has_permissions(send_messages=True)
    async def topic(self, ctx:utils.Context):
        """
        The parent group for the topic commands.
        """

        async with self.bot.database() as db:
            rows = await db("SELECT * FROM topics ORDER BY RANDOM() LIMIT 1")
        if not rows:
            return await ctx.send("There aren't any topics set up in the database for this bot :<")
        return await ctx.send(rows[0]['topic'])

    @topic.command(name="get")
    @commands.bot_has_permissions(send_messages=True)
    async def topic_get(self, ctx:utils.Context):
        """
        Gives you a conversation topic.
        """

        async with self.bot.database() as db:
            rows = await db("SELECT * FROM topics ORDER BY RANDOM() LIMIT 1")
        if not rows:
            return await ctx.send("There aren't any topics set up in the database for this bot :<")
        return await ctx.send(rows[0]['topic'])

    @topic.command(name="add")
    @utils.checks.is_bot_support()
    @commands.bot_has_permissions(send_messages=True)
    async def topic_add(self, ctx:utils.Context, *, topic:str):
        """
        Add a new topic to the database.
        """

        async with self.bot.database() as db:
            await db("INSERT INTO topics VALUES ($1)", topic)
        return await ctx.send("Added to database.")

    @utils.command()
    @commands.bot_has_permissions(send_messages=True)
    async def coinflip(self, ctx:utils.Context):
        """
        Flips a coin.
        """

        coin = ["Heads", "Tails"]
        return await ctx.send(random.choice(coin))

    @utils.command(aliases=['http'])
    @utils.cooldown.cooldown(1, 5, commands.BucketType.channel)
    async def httpcat(self, ctx:utils.Context, errorcode:str):
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

        await ctx.channel.trigger_typing()
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
        with utils.Embed(use_random_colour=True) as embed:
            embed.set_image(url=f'https://http.cat/{errorcode}')
        await ctx.send(embed=embed)

    @utils.command()
    @utils.cooldown.cooldown(1, 5, commands.BucketType.channel)
    async def httpdog(self, ctx:utils.Context, errorcode:str):
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

        await ctx.channel.trigger_typing()
        headers = {"User-Agent": self.bot.user_agent}
        async with self.bot.session.get(f"https://httpstatusdogs.com/img/{errorcode}.jpg",
                                        headers=headers, allow_redirects=False) as r:
            if str(r.status)[0] != "2":
                if errorcode not in standard_errorcodes:
                    await ctx.send("That HTTP code doesn't exist.")
                else:
                    await ctx.send('Image for HTTP code not found on provider.')
                return
        with utils.Embed(use_random_colour=True) as embed:
            embed.set_image(url=f'https://httpstatusdogs.com/img/{errorcode}.jpg')
        await ctx.send(embed=embed)

    @utils.command(aliases=['color'], add_slash_command=False)
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def colour(self, ctx:utils.Context, *, colour:typing.Union[utils.converters.ColourConverter, discord.Role, discord.Member]):
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
        with utils.Embed(colour=hex_colour,title=f"#{hex_colour:0>6X}") as embed:
            embed.set_image(url=f"https://www.htmlcsscolor.com/preview/gallery/{hex_colour:0>6X}.png")
        await ctx.send(embed=embed)

    @utils.command(cooldown_after_parsing=True)
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(send_messages=True)
    @utils.cooldown.cooldown(1, 60, commands.BucketType.guild)
    async def spam(self, ctx:utils.Context, amount:int, *, text:str):
        """
        Spams a message a given amount of times.
        """

        if amount > 10:
            return await ctx.send("That's too much to spam.")
        for _ in range(amount):
            await ctx.send(text)

    @utils.command(aliases=['disconnectvc', 'clearvc'])
    @commands.has_guild_permissions(move_members=True)
    @commands.bot_has_guild_permissions(move_members=True)
    @commands.bot_has_permissions(send_messages=True)
    async def emptyvc(self, ctx:utils.Context, channel:discord.VoiceChannel):
        """
        Removes all the people from a given VC.
        """

        if not channel.members:
            return await ctx.send("There are no people in that VC for me to remove.")
        member_count = len(channel.members)
        for member in channel.members:
            try:
                await member.edit(voice_channel=None)
            except discord.Forbidden:
                return await ctx.send("I don't have permission to remove members from that channel.")
        return await ctx.send(f"Dropped {member_count} members from the VC.")

    @utils.command()
    @commands.bot_has_permissions(send_messages=True)
    async def buttons(self, ctx: utils.Context):
        """
        Makes a cute lil message of clickable buttons.
        """

        def make_button(i):
            return utils.Button("X", f"DISABLE_BUTTON_COMMAND {i}", style=utils.ButtonStyle(random.randint(1, 4)))
        await ctx.send(
            "OwO button time",
            components=utils.MessageComponents.add_buttons_with_rows(
                *[make_button(i) for i in range(25)]
            ),
        )

    @utils.Cog.listener()
    async def on_button_click(self, payload):
        """
        Disables a given button.
        """

        if not payload.component.custom_id.startswith("DISABLE_BUTTON_COMMAND"):
            return
        components = utils.MessageComponents(*[
            utils.ActionRow(*[
                utils.Button.from_dict(b) for b in r['components']
            ]) for r in payload.data['message']['components']
        ])
        b = components.get_component(payload.component.custom_id)
        b.disable()
        await payload.ack()
        await payload.message.edit(components=components)


def setup(bot:utils.Bot):
    x = MiscCommands(bot)
    bot.add_cog(x)
