import io
from datetime import datetime as dt
import typing

import discord
from discord.ext import commands
import voxelbotutils as utils


class UserInfo(utils.Cog):

    @utils.command(aliases=["avatar", "av"])
    async def enlarge(self, ctx:utils.Context, target:typing.Union[discord.User, discord.PartialEmoji]=None):
        """
        Enlarges the avatar or given emoji.
        """

        target = target or ctx.author
        if isinstance(target, (discord.User, discord.Member)):
            url = target.avatar_url
        elif isinstance(target, (discord.Emoji, discord.PartialEmoji)):
            url = target.url
        with utils.Embed(color=0x1) as embed:
            embed.set_image(url=str(url))
        await ctx.send(embed=embed)

    @utils.command(aliases=["whoami"])
    async def whois(self, ctx:utils.Context, user:discord.Member=None):
        """
        Give you some information about a user.
        """

        user = user or ctx.author
        with utils.Embed(use_random_colour=True) as embed:
            embed.set_author_to_user(user)
            account_creation_time_humanized = utils.TimeValue((dt.utcnow() - user.created_at).total_seconds()).clean_full
            create_value = f"{user.created_at.strftime('%A %B %d %Y %I:%M:%S%p')}\n{account_creation_time_humanized} ago"
            embed.add_field("Account Creation Time", create_value, inline=False)
            guild_join_time_humanized = utils.TimeValue((dt.utcnow() - user.joined_at).total_seconds()).clean_full
            join_value = f"{user.joined_at.strftime('%A %B %d %Y %I:%M:%S%p')}\n{guild_join_time_humanized} ago"
            embed.add_field("Guild Join Time", join_value, inline=False)
            embed.set_thumbnail(user.avatar_url_as(size=1024))
        return await ctx.send(embed=embed)

    @utils.command()
    @commands.guild_only()
    async def createlog(self, ctx:utils.Context, amount:int=100):
        """
        Create a log of chat.
        """

        # Create the data we're gonna send
        data = {
            "channel_name": ctx.channel.name,
            "category_name": ctx.channel.category.name,
            "guild_name": ctx.guild.name,
            "guild_icon_url": str(ctx.guild.icon_url),
        }
        data_authors = {}
        data_messages = []

        # Get the data from the server
        async for message in ctx.channel.history(limit=min([max([1, amount]), 250])):
            for user in message.mentions + [message.author]:
                data_authors[user.id] = {
                    "username": user.name,
                    "discriminator": user.discriminator,
                    "avatar_url": str(user.avatar_url),
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
                # "embeds": [i.to_dict() for i in message.embeds],
            }
            embeds = []
            for i in message.embeds:
                embed_data = i.to_dict()
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


def setup(bot:utils.Bot):
    x = UserInfo(bot)
    bot.add_cog(x)
