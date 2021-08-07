import json

import discord
from discord.ext import commands
import voxelbotutils as vbu


class MessageInfo(vbu.Cog):

    @vbu.command()
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(send_messages=True)
    async def dumpmessage(self, ctx: vbu.Context, message: discord.Message):
        """
        Dumps a message out into chat.
        """

        await ctx.send(f'```\n{message.content}\n```')

    @vbu.command(aliases=['dumpmessageembed'], add_slash_command=False)
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(send_messages=True)
    async def dumpmessageembeds(self, ctx: vbu.Context, message: discord.Message):
        """
        Dumps a message out into chat.
        """

        await ctx.send(f'```json\n{json.dumps([i.to_dict() for i in message.embeds], indent=2)}\n```')

    @vbu.command(add_slash_command=False)
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(send_messages=True)
    async def dumpmessagelist(self, ctx: vbu.Context, message: discord.Message):
        """
        Dumps a message out into chat.
        """

        await ctx.send(f'```py\n{[i.encode("unicode_escape").decode() for i in list(message.content)]}\n```')


def setup(bot: vbu.Bot):
    x = MessageInfo(bot)
    bot.add_cog(x)
