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
       
    @utils.command(aliases=['removeemoji', 'delemoji'])
    @commands.bot_has_permissions(manage_emojis=True)
    @commands.has_guild_permissions(manage_emojis=True)
    @commands.guild_only()
    async def deleteemoji(self, ctx:utils.Context, emoji:typing.Union[discord.PartialEmoji, int]):
        """
        Deletes an emoji from a server
        """
        
        # If the emoji provided is just an ID, find the emoji
        if isintance(emoji, int):
            emoji = self.bot.get_emoji(emoji)
        
        if (not emoji) or (emoji not in ctx.guild.emojis):
            raise commands.BadArgument("The emoji you provided either does not exist or is not in this server.")
        
        emoji_name = emoji.name
        await emoji.delete()
        await ctx.send(f"Deleted emoji `emoji_name`.")
    
    @utils.command(aliases=['addemoji'])
    @commands.bot_has_permissions(manage_emojis=True)
    @commands.has_guild_permissions(manage_emojis=True)
    @commands.guild_only()
    async def stealemoji(self, ctx:utils.Context, emoji:typing.Optional[typing.Union[discord.PartialEmoji, int, ImageUrl]]=None, name:str=None, animated:bool=False):
        """
        Copies an emoji and uploads it to your server.
        """

        # Default to the first attachment in the message's URL if `emoji` (the image url) is None
        if emoji is None:
            if ctx.message.attachments:
                emoji = ctx.message.attachments[0].url
                await ImageUrl().convert(ctx, emoji)  # Make sure the url is an image
            else:
                raise utils.errors.MissingRequiredArgumentString("emoji")

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
