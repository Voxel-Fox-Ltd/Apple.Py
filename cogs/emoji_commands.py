import typing
import re

import discord
from discord.ext import commands
import voxelbotutils as utils


class ImageUrl(commands.Converter):

    regex = re.compile(r"(http(s?):)([/|.|\w|\s|-])*\.(?:jpg|gif|png)")

    async def convert(self, ctx:utils.Context, argument:str):
        """
        Make sure a given string argument is an image URL.
        """

        v = self.regex.search(argument)
        if v is None:
            raise commands.BadArgument()
        return argument


class EmojiCommands(utils.Cog):

    @utils.command(aliases=['addemoji'])
    @commands.bot_has_permissions(manage_emojis=True)
    @commands.has_guild_permissions(manage_emojis=True)
    @commands.guild_only()
    async def stealemoji(self, ctx:utils.Context, emoji:typing.Union[discord.PartialEmoji, int, ImageUrl], name:str=None, animated:bool=False):
        """
        Copies an emoji and uploads it to your server.
        """

        # See if we gave an emoji ID
        if isinstance(emoji, int):
            if name is None:
                raise utils.errors.MissingRequiredArgumentString("name")
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

        # Upload that to Discord
        try:
            e = await ctx.guild.create_custom_emoji(name=name, image=data)
        except discord.HTTPException as e:
            return await ctx.send(f"I couldn't create that emoji - {e}")
        except discord.InvalidArgument:
            return await ctx.send("Unsupported image type - make sure you're providing the correct argument for the image's animation state.")
        await ctx.send(f"Emoji added - {e!s}")


def setup(bot:utils.Bot):
    x = EmojiCommands(bot)
    bot.add_cog(x)
