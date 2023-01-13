import typing
import asyncio
import functools

import discord
from discord.ext import commands, vbu
from bs4 import BeautifulSoup
import imgkit


class UserInfo(vbu.Cog):

    @commands.command(
        aliases=["avatar", "av"],
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="target",
                    description="The item that you want to enlarge.",
                    type=discord.ApplicationCommandOptionType.string,
                ),
            ],
        ),
    )
    async def enlarge(
            self,
            ctx: vbu.Context,
            target: discord.Member | discord.User | discord.Emoji | discord.PartialEmoji):
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

    @commands.context_command(name="Get user info")
    async def _get_user_info(self, ctx: vbu.SlashContext, user: discord.Member):
        command = self.whois
        await command.can_run(ctx)
        await ctx.invoke(command, user)

    @commands.command(
        aliases=["whoami"],
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="user",
                    description="The user you want to get the information of.",
                    type=discord.ApplicationCommandOptionType.user,
                    required=False,
                ),
            ],
        ),
    )
    async def whois(
            self,
            ctx: vbu.Context,
            user: typing.Optional[discord.Member] = None):
        """
        Give you some information about a user.
        """

        # Set up our intial vars
        user = user or ctx.author
        assert user is not None
        embed = vbu.Embed(use_random_colour=True)
        embed.set_author_to_user(user)

        # Get the user account creation time
        create_value = (
            f"{discord.utils.format_dt(user.created_at)}\n"
            f"{discord.utils.format_dt(user.created_at, 'R')}"
        )
        embed.add_field("Account Creation Time", create_value, inline=False)

        # Get the user guild join time
        if user.joined_at:
            join_value = (
                f"{discord.utils.format_dt(user.joined_at)}\n"
                f"{discord.utils.format_dt(user.joined_at, 'R')}"
            )
            embed.add_field("Guild Join Time", join_value, inline=False)

        # Set the embed thumbnail
        embed.set_thumbnail(user.display_avatar.with_size(1024).url)

        # Sick
        if isinstance(ctx, commands.SlashContext):
            return await ctx.interaction.response.send_message(embed=embed)
        else:
            return await ctx.send(embed=embed)

    @commands.context_command(name="Screenshot message")
    @commands.guild_only()
    async def _context_command_screenshot_message(
            self,
            ctx: vbu.Context,
            message: discord.Message):
        command = self.fakemessage
        await command.can_run(ctx)
        await ctx.invoke(command, user=message.author, content=message)

    @commands.command(
        aliases=["screenshotmessage"],
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="user",
                    description="The user who you want to fake a message from.",
                    type=discord.ApplicationCommandOptionType.user,
                ),
                discord.ApplicationCommandOption(
                    name="content",
                    description="The content that you want in the message.",
                    type=discord.ApplicationCommandOptionType.string,
                ),
            ],
        ),
    )
    @commands.defer()
    @commands.guild_only()
    async def fakemessage(
            self,
            ctx: vbu.Context,
            user: discord.Member,
            *,
            content: str | discord.Message):
        """
        Create a log of chat.
        """

        # See if we're getting a real message or a fake one
        content_message = ctx.message
        if isinstance(content, discord.Message):
            content_message = content
            user = content.author
            content = content.content
        assert isinstance(content_message.channel, discord.TextChannel)
        assert content_message.guild

        # Create the data we're gonna send
        data = {
            "channel_name": content_message.channel.name,
            "category_name": (
                content_message.channel.category.name
                if content_message.channel.category
                else "Uncategorized"
            ),
            "guild_name": content_message.guild.name,
            "guild_icon_url": (
                (
                    content_message
                    .guild.icon
                    .with_format("png")
                    .with_size(512)
                    .url
                )
                if content_message.guild.icon
                else None
            ),
        }
        data_authors = {}
        data_authors[user.id] = {
            "username": user.name,
            "discriminator": user.discriminator,
            "avatar_url": (
                user
                .display_avatar
                .with_size(512).
                with_format("png")
                .url
            ),
            "bot": user.bot,
            "display_name": user.display_name,
            "color": user.colour.value,
        }
        for i in content_message.mentions:
            data_authors[i.id] = {
                "username": i.name,
                "discriminator": i.discriminator,
                "avatar_url": (
                    i
                    .display_avatar
                    .with_size(512)
                    .with_format("png")
                    .url
                ),
                "bot": i.bot,
                "display_name": i.display_name,
                "color": i.colour.value,
            }
        message_data = {
            "id": 69,
            "content": content,
            "author_id": user.id,
            "timestamp": int(discord.utils.utcnow().timestamp()),
        }

        # Send data to the API
        data.update({"users": data_authors, "messages": [message_data]})
        resp = await self.bot.session.post(
            "https://voxelfox.co.uk/discord/chatlog",
            json=data,
        )
        string = await resp.text()

        # Remove the preamble
        soup = BeautifulSoup(string, "html.parser")
        pre = soup.find(class_="preamble")
        pre.decompose()
        subset = str(soup)

        # Screenshot it
        options = {
            "quiet": "",
            "enable-local-file-access": "",
            "width": "600",
            "enable-javascript": "",
            "javascript-delay": "1000",
        }
        filename = f"FakedMessage-{ctx.author.id}.png"
        from_string = functools.partial(
            imgkit.from_string,
            subset,
            filename,
            options=options,
        )
        await self.bot.loop.run_in_executor(None, from_string)

        # Output and delete temp
        await ctx.send(file=discord.File(filename))
        await asyncio.sleep(1)
        await asyncio.create_subprocess_exec("rm", filename)


def setup(bot: vbu.Bot):
    x = UserInfo(bot)
    bot.add_cog(x)
