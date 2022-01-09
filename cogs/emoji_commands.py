import typing
import re
import io
import asyncio

import discord
from discord.ext import commands, vbu
from PIL import Image

from .types.bot import Bot


class ImageUrl(commands.Converter):

    __application_option_type__ = discord.ApplicationCommandOptionType.string
    regex = re.compile(r"(http(s?):)([/|.|\w|\s|-])*\.(?:jpg|gif|png)")

    async def convert(self, ctx: vbu.Context, argument: str):
        """
        Make sure a given string argument is an image URL.
        """

        v = self.regex.search(argument)
        if v is None:
            raise commands.BadArgument()
        return argument


class EmojiCommands(vbu.Cog[Bot]):

    EMOJI_REGEX = re.compile(r'<(a?):([a-zA-Z0-9\_]{1,32}):([0-9]{15,20})>')

    @commands.context_command(name="Add emoji from message")
    async def add_emojis_from_message(self, ctx: commands.SlashContext, message: discord.Message):
        """
        Search the emojis in a message and ask the user which they want to add.
        """

        # Run all of our checks
        await commands.guild_only().predicate(ctx)
        await commands.bot_has_permissions(manage_emojis=True).predicate(ctx)
        await commands.has_permissions(manage_emojis=True).predicate(ctx)

        # Check the message for emojis - stolen from partialemojiconverter
        matches = self.EMOJI_REGEX.finditer(message.content)
        emojis = [
            discord.PartialEmoji(name=i.group(2), animated=i.group(1) == "a", id=int(i.group(3)))
            for i in matches
        ]

        # Make sure there's some emojis
        if len(emojis) == 0:
            return await ctx.interaction.response.send_message(
                "I failed to find any emojis in that message.",
                ephemeral=True,
            )

        # If there's only one that's even EASIER
        elif len(emojis) == 1:
            await ctx.interaction.response.defer()
            return await self.addemoji(ctx, emojis[0])

        # If there's more than 25 that's just fucked
        elif len(emojis) > 25:
            return await ctx.interaction.response.send_message(
                "There's more than 25 emojis in that message. Hate that.",
                ephemeral=True,
            )

        # But otherwise we'll need to ask which one
        components = discord.ui.MessageComponents(
            discord.ui.ActionRow(
                (sm := discord.ui.SelectMenu(
                    options=[
                        discord.ui.SelectOption(label=i.name, emoji=i, value=str(i))
                        for i in emojis
                    ]
                ))
            )
        )
        await ctx.interaction.response.send_message(
            "Which emoji do you want to add to your server?",
            components=components,
        )

        # So now wait for em to respond
        try:
            select_interaction: discord.Interaction[str]
            select_interaction = await self.bot.wait_for(
                "component_interaction",
                check=lambda i: i.user.id == ctx.author.id and i.custom_id.endswith(sm.custom_id),
                timeout=60 * 2,
            )
        except asyncio.TimeoutError:
            try:
                await ctx.interaction.edit_original_message(
                    content="Didn't get a response in time.",
                    components=None,
                )
            except:
                pass
            return

        # And continue with whatever they said
        await select_interaction.response.defer_update()
        ctx.interaction = select_interaction
        assert select_interaction.values
        match = self.EMOJI_REGEX.search(select_interaction.values[0])
        assert match
        emoji = discord.PartialEmoji(name=match.group(2), animated=match.group(1) == "a", id=int(match.group(2)))
        await self.addemoji(ctx, emoji)

    @staticmethod
    def calculate_new_size(image: Image.Image, intended_size: int = 256_000) -> tuple:
        """
        Use the equation f(n) = n * h * w * c to calculate an image's size given a size modifier, the width, the height,
        and a calculated constant. This method is inaccurate because image compression isn't constant, but it's as close
        as we care to get.
        """

        width = image.width
        height = image.height
        initial_size = len(image.tobytes())
        magic_constant = (initial_size) / (width * height)  # The constant (c)
        size_mod = intended_size / (magic_constant * width * height)  # The size modifier to reach the intended size

        return (int(width * size_mod), int(height * size_mod))

    @commands.command(
        aliases=['stealemoji'],
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="emoji",
                    description="The emoji that you want to add.",
                    type=discord.ApplicationCommandOptionType.string,
                ),
                discord.ApplicationCommandOption(
                    name="name",
                    description="The name of the emoji.",
                    type=discord.ApplicationCommandOptionType.string,
                    required=False,
                ),
                discord.ApplicationCommandOption(
                    name="animated",
                    description="Whether or not the emoji is animated.",
                    type=discord.ApplicationCommandOptionType.boolean,
                    required=False
                ),
            ],
        ),
    )
    @commands.defer()
    @commands.bot_has_permissions(manage_emojis=True)
    @commands.has_guild_permissions(manage_emojis=True)
    @commands.guild_only()
    async def addemoji(
            self,
            ctx: vbu.Context,
            emoji: typing.Optional[typing.Union[discord.PartialEmoji, int, ImageUrl]] = None,
            name: str = None,
            animated: bool = False,
            ):
        """
        Copies an emoji and uploads it to your server.
        """

        # Default to the first attachment in the message's URL if `emoji` (the image url) is None
        if emoji is None:
            if ctx.message.attachments:
                emoji = ctx.message.attachments[0].url
                await ImageUrl().convert(ctx, emoji)  # Make sure the url is an image
            else:
                raise vbu.errors.MissingRequiredArgumentString("emoji")

        # See if we gave an emoji ID
        if isinstance(emoji, int):
            if name is None:
                raise vbu.errors.MissingRequiredArgumentString("name")
            emoji = discord.PartialEmoji(name=name, animated=animated, id=emoji)

        # See if we gave an image URL or an emoji
        if isinstance(emoji, discord.PartialEmoji):
            url = str(emoji.url)
            name = name or emoji.name
        else:
            url = emoji

        # Grab image data
        async with self.bot.session.get(url) as r:
            data = await r.read()

        # If the size is too big for Discord
        if len(data) > 256_000:
            original_image = Image.open(io.BytesIO(data))
            new_size = self.calculate_new_size(original_image)
            resized_image = original_image.resize(new_size)  # .tobytes()
            new_image_file_handle = io.BytesIO()
            resized_image.save(new_image_file_handle, format="png")
            new_image_file_handle.seek(0)
            data = new_image_file_handle.read()

        # Upload that to Discord
        try:
            e = await ctx.guild.create_custom_emoji(name=name, image=data)
        except discord.HTTPException as e:
            return await ctx.send(f"I couldn't create that emoji - {e}")
        except discord.InvalidArgument:
            return await ctx.send("Unsupported image type - make sure you're providing the correct argument for the image's animation state.")
        await ctx.send(f"Emoji added - {e!s}")


def setup(bot: Bot):
    x = EmojiCommands(bot)
    bot.add_cog(x)
