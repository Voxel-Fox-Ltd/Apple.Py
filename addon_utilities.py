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

    def is_bot_no_limit(self, m):
        if m.author == self.bot.user or (m.content[0] == '.' and m.content[1].lower() in 'abcdefghijklmnopqrstuvwxyz'):
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
        try:
            await self.bot.say(' '.join(x))
        except:
            await self.bot.say("There's nobody in that VC smh")


    @commands.command(pass_context=True, help=helpText['clean'][1], brief=helpText['clean'][0])
    async def clean(self, ctx):
        """Deletes the bot's messages from the last 50 posted to the channel."""
        counter = 0
        try:
            if ctx.message.content.split(' ')[1].lower() == 'true':
                # q = await self.bot.purge_from(ctx.message.channel, limit=50, check=self.is_bot_no_limit)
                async for i in self.bot.logs_from(ctx.message.channel, limit=50):
                    try:
                        if i.author == self.bot.user or (i.content[0] == '.' and i.content[1].lower() in 'abcdefghijklmnopqrstuvwxyz'):
                            await self.bot.delete_message(i)
                            counter += 1
                    except:
                        pass
                await self.bot.say("Cleaned up **{}** messages".format(counter))
                return
        except:
            pass

        # q = await self.bot.purge_from(ctx.message.channel, limit=50, check=self.is_bot)
        async for i in self.bot.logs_from(ctx.message.channel, limit=50):
            if i.author.id == self.bot.user.id:
                await self.bot.delete_message(i)
                counter += 1
        await self.bot.say("Cleaned up **{}** messages".format(counter))


def setup(bot):
    bot.add_cog(Utilities(bot))
