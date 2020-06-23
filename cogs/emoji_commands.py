import typing

import discord
from discord.ext import commands

from cogs import utils


class EmojiCommands(utils.Cog):

    @commands.command(cls=utils.Command)
    @commands.bot_has_permissions(manage_emojis=True)
    @commands.has_guild_permissions(manage_emojis=True)
    @commands.guild_only()
    async def stealemoji(self, ctx:utils.Context, emoji:typing.Union[discord.PartialEmoji, int], name:str=None, animated:bool=False):
        """Copies an emoji and uploads it to your server"""

        if isinstance(emoji, int):
            if name is None:
                raise utils.errors.MissingRequiredArgumentString("name")
            emoji = discord.PartialEmoji(name=name, animated=animated, id=emoji)

        url = str(emoji.url)
        async with self.bot.session.get(url) as r:
            data = await r.read()
        try:
            e = await ctx.guild.create_custom_emoji(name=name or emoji.name, image=data)
        except discord.HTTPException as e:
            return await ctx.send(f"I couldn't create that emoji - {e}")
        await ctx.send(f"Emoji added - {e!s}")


def setup(bot:utils.Bot):
    x = EmojiCommands(bot)
    bot.add_cog(x)
