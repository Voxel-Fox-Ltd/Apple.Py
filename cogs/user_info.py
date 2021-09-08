import io
from datetime import datetime as dt
import typing
import asyncio
import functools

import discord
from discord.ext import commands, vbu
from bs4 import BeautifulSoup
import imgkit


class UserInfo(vbu.Cog):

    @commands.command(aliases=["avatar", "av"])  # Added as context commands
    async def enlarge(self, ctx: vbu.Context, target: typing.Union[discord.Member, discord.User, discord.Emoji, discord.PartialEmoji] = None):
        """
        Enlarges the avatar or given emoji.
        """

        target = target or ctx.author
        if isinstance(target, (discord.User, discord.Member, discord.ClientUser)):
            url = target.display_avatar.url
        elif isinstance(target, (discord.Emoji, discord.PartialEmoji)):
            url = target.url
        with vbu.Embed(color=0x1) as embed:
            embed.set_image(url=str(url))
        await ctx.send(embed=embed)

    @commands.command(aliases=["whoami"])  # Added as context commands
    async def whois(self, ctx: vbu.Context, user: discord.Member = None):
        """
        Give you some information about a user.
        """

        # Set up our intial vars
        user = user or ctx.author
        embed = vbu.Embed(use_random_colour=True)
        embed.set_author_to_user(user)

        # Get the user account creation time
        create_value = f"{discord.utils.format_dt(user.created_at)}\n{discord.utils.format_dt(user.created_at, 'R')}"
        embed.add_field("Account Creation Time", create_value, inline=False)

        # Get the user guild join time
        if ctx.guild:
            join_value = f"{discord.utils.format_dt(user.joined_at)}\n{discord.utils.format_dt(user.joined_at, 'R')}"
            embed.add_field("Guild Join Time", join_value, inline=False)

        # Set the embed thumbnail
        embed.set_thumbnail(user.display_avatar.with_size(1024).url)

        # Sick
        return await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    async def createlog(self, ctx: vbu.Context, amount: int = 100):
        """
        Create a log of chat.
        """

        # Make some assertions so we don't get errors elsewhere
        assert isinstance(ctx.channel, discord.TextChannel)
        assert ctx.guild

        # Create the data we're gonna send
        data = {
            "channel_name": ctx.channel.name,
            "category_name": ctx.channel.category.name if ctx.channel.category else "Uncategorized",
            "guild_name": ctx.guild.name,
            "guild_icon_url": ctx.guild.icon.url if ctx.guild.icon else None,
        }
        data_authors = {}
        data_messages = []

        # Get the data from the server
        async for message in ctx.channel.history(limit=min([max([1, amount]), 250])):
            for user in message.mentions + [message.author]:
                data_authors[user.id] = {
                    "username": user.name,
                    "discriminator": user.discriminator,
                    "avatar_url": str(user.display_avatar.url),
                    "bot": user.bot,
                    "display_name": user.display_name,
                    "color": user.colour.value,
                }
            message_data = {
                "id": message.id,
                "content": message.content,
                "author_id": message.author.id,
                "timestamp": int(message.created_at.timestamp()),
                "attachments": [str(i.url) for i in message.attachments],
            }
            embeds = []
            for i in message.embeds:
                embed_data: dict = i.to_dict()  # type: ignore
                if i.timestamp:
                    embed_data.update({'timestamp': i.timestamp.timestamp()})
                embeds.append(embed_data)
            message_data.update({'embeds': embeds})
            data_messages.append(message_data)

        # Send data to the API
        data.update({"users": data_authors, "messages": data_messages[::-1]})
        async with self.bot.session.post("https://voxelfox.co.uk/discord/chatlog", json=data) as r:
            string = io.StringIO(await r.text())

        # Output it into the chat
        await ctx.send(file=discord.File(string, filename=f"Logs-{int(ctx.message.created_at.timestamp())}.html"))

    @commands.command()
    @commands.guild_only()
    async def fakemessage(self, ctx: vbu.Context, user: discord.Member, *, content: str):
        """
        Create a log of chat.
        """

        # Make some assertions so we don't get errors elsewhere
        assert isinstance(ctx.channel, discord.TextChannel)
        assert ctx.guild

        # Create the data we're gonna send
        data = {
            "channel_name": ctx.channel.name,
            "category_name": ctx.channel.category.name if ctx.channel.category else "Uncategorized",
            "guild_name": ctx.guild.name,
            "guild_icon_url": ctx.guild.icon.url if ctx.guild.icon else None,
        }
        data_authors = {}
        data_authors[user.id] = {
            "username": user.name,
            "discriminator": user.discriminator,
            "avatar_url": str(user.display_avatar.with_size(512).url),
            "bot": user.bot,
            "display_name": user.display_name,
            "color": user.colour.value,
        }
        message_data = {
            "id": 69,
            "content": content,
            "author_id": user.id,
            "timestamp": int(discord.utils.utcnow().timestamp()),
        }

        # Send data to the API
        data.update({"users": data_authors, "messages": [message_data]})
        async with self.bot.session.post("https://voxelfox.co.uk/discord/chatlog", json=data) as r:
            string = await r.text()
        soup = BeautifulSoup(string, "html.parser")
        soup.find(class_="preamble").decompose()
        subset = str(soup)

        # Screenshot it
        options = {"quiet": "", "enable-local-file-access": "", "width": "0"}
        filename = f"FakedMessage-{ctx.author.id}.png"
        from_string = functools.partial(imgkit.from_string, subset, filename, options=options)
        await self.bot.loop.run_in_executor(None, from_string)

        # Output it into the chat
        await ctx.send(file=discord.File(filename))

        # And delete file
        await asyncio.sleep(1)
        await asyncio.create_subprocess_exec("rm", filename)


def setup(bot: vbu.Bot):
    x = UserInfo(bot)
    bot.add_cog(x)
