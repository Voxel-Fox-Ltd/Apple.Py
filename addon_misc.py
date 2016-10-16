from isAllowed import *


BOT_CLIENT_ID = tokens['SkybotID']


class Misc:

    def __init__(self, bot):
        self.bot = bot


    @commands.command()
    async def git(self):
        """Plonks the link to my Github in chat."""
        await self.bot.say("Feel free to fork me!\n<https://github.com/4Kaylum/Apple.py>")


    @commands.command(pass_context=True, help=helpText['invite'][1], brief=helpText['invite'][0])
    async def invite(self, ctx):
        """Gives the invite link for the bot."""
        print("Told someone the invite link.")
        q = "https://discordapp.com/oauth2/authorize?scope=bot&client_id=%s&permissions=0xFFFFFFFF" \
            % BOT_CLIENT_ID
        await self.bot.say(q)


    @commands.command(pass_context=True, help=helpText['echo'][1], brief=helpText['echo'][0])
    async def echo(self, ctx):
        """Simply says back what the person says."""
        print("Echoing :: %s" % ctx.message.content.split(' ', 1)[1])
        try:
            chan = discord.Object(ctx.message.raw_channel_mentions[0])
            a = ctx.message.content.split(' ', 2)[2]
        except:
            chan = ctx.message.channel
            a = ctx.message.content.split(' ', 1)[1]
        await self.bot.send_message(chan, a)


    @commands.command(pass_context=True, help=helpText['uptime'][1], brief=helpText['uptime'][0])
    async def uptime(self, ctx):
        """Shows the uptime of the bot."""
        now = datetime.datetime.now()
        up = now - startTime

        up = int(up.total_seconds())
        hours = up // 3600
        up -= hours * 3600
        minutes = up // 60
        up -= minutes * 60

        out = '''```%s hours
%s minutes
%s seconds```''' % (hours, minutes, up)

        userCount = []
        for i in self.bot.servers:
            for o in i.members:
                if o not in userCount:
                    userCount.append(o)

        outplut = '''```On %s servers
Serving %s unique users```''' % (len(self.bot.servers), len(userCount))

        superOut = outplut + '\n' + out
        await self.bot.say(superOut)


    @commands.command(pass_context=True)
    async def getpins(self, ctx):
        pinMes = await self.bot.pins_from(ctx.message.channel)
        if len(pinMes) == 0:
            await self.bot.say("There are no pins for this channel defined.")
            return
        pinCon = [i.content for i in pinMes]
        pinCon.remove('')
        q = '```\n' + '\n```\n```\n'.join(pinCon) + '\n```'
        try:
            await self.bot.say(q)
        except:
            await self.bot.say("There are too many pins to fit into one message .-.")


    @commands.command(pass_context=True)
    async def createinvite(self, ctx):
        try:
            serverID = ctx.message.content.split(' ',1)[1]
        except IndexError:
            await self.bot.say('Provide a server ID to give an invite to.')
            return

        server = self.bot.get_server(serverID)
        if server == None:
            await self.bot.say("I could not find a server with that ID.")
            return

        try:
            inv = await self.bot.create_invite(server)
        except:
            await self.bot.say('I could not create the server invite - missing permissions?')
            return
        await self.bot.say(inv.url)


    @commands.command(pass_context=True,hidden=True,enabled=False)
    async def tts(self, ctx):
        await self.bot.send_message(ctx.message.channel, ctx.message.content.split(' ',1)[1],tts=True)



def setup(bot):
    bot.add_cog(Misc(bot))
