import discord
from discord.ext import commands
from isAllowed import *


class Utilities:

    def __init__(self, bot):
        self.bot = bot


    def is_bot(self, m):
        if m.author == self.bot.user:
            if m.content.startswith('Cleaned up'):
                return False
            else:
                return True


    @commands.command(pass_context=True)
    async def ping(self, ctx):
        channelName = ctx.message.content.split(' ',1)[1]
        channel = discord.utils.get(ctx.message.server.channels, name=channelName, type=discord.ChannelType.voice)
        if channel == None:
            await self.bot.say("I could not find a VC under that name.")
            return
        x = []
        for i in channel.voice_members:
            x.append(i.mention)
        await self.bot.say(' '.join(x))


    @commands.command(pass_context=True, help=helpText['clean'][1], brief=helpText['clean'][0])
    async def clean(self, ctx):
        """Deletes the bot's messages from the last 50 posted to the channel."""
        q = await self.bot.purge_from(ctx.message.channel, limit=50, check=self.is_bot)
        await self.bot.say("Cleaned up **{}** messages".format(len(q)))


def setup(bot):
    bot.add_cog(Utilities(bot))
