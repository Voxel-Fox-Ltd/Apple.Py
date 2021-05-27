import discord
from discord.ext import commands
import voxelbotutils as utils


class MessageInfo(utils.Cog):

    @utils.command()
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(send_messages=True)
    async def dumpmessage(self, ctx:utils.Context, message:discord.Message):
        """
        Dumps a message out into chat.
        """

        await ctx.send(f'```\n{message.content}\n```')

    @utils.command(aliases=['dumpmessageembed'])
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(send_messages=True)
    async def dumpmessageembeds(self, ctx:utils.Context, message:discord.Message):
        """
        Dumps a message out into chat.
        """

        await ctx.send(f'```json\n{json.dumps([i.to_dict() for i in message.embeds], indent=2)}\n```')

    @utils.command()
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(send_messages=True)
    async def dumpmessagelist(self, ctx:utils.Context, message:discord.Message):
        """
        Dumps a message out into chat.
        """

        await ctx.send(f'```py\n{[i.encode("unicode_escape").decode() for i in list(message.content)]}\n```')


def setup(bot: utils.Bot):
    x = MessageInfo(bot)
    bot.add_cog(x)
