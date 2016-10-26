from isAllowed import *


class Voice():


    def __init__(self, bot):
        self.bot = bot
        self.voice = {}
        if not discord.opus.is_loaded():
            discord.opus.load_opus()
        for i in self.bot.servers:
            # Voice[serverID] = [DiscordVoiceClient, [YTDLStreamPlayer], ChannelToTalkIn, Volume]
            self.voice[i.id] = [self.bot.voice_client_in(i), None, None]


    async def musicMan(self, ctx, searchTerm):
        # termOne = ['fuck','fuk','fukc','fuck','fuq','faq'] # ['please','plx','plz','pl0x','pliz']
        # termTwo = ['george','gozzy','auguste','aughuste','auguste','auguste','gervase','gervaise'] # ['sir','master','daddy','mr','daddy-kun']
        # if ctx.message.author.id != '141231597155385344':
        #     if searchTerm.split(' ')[-2].lower() not in termOne or searchTerm.split(' ')[-1].lower() not in termTwo:
        #         await self.bot.say("Say '{} {}' ;3".format(termOne[0], termTwo[0]))
        #         return
        #     else:
        #         if random.randint(0,100) == 2:
        #             await self.bot.say('No. Fuck yourself.')
        #             return
        #         qw = searchTerm.split(' ')
        #         del qw[-1]
        #         del qw[-1]
        #         # del qw[-1]
        #         searchTerm = ' '.join(qw)

        self.voice[ctx.message.server.id][2] = ctx.message.channel
        try:
            self.voice[ctx.message.server.id][0] = await self.bot.join_voice_channel(ctx.message.author.voice_channel)
        except discord.InvalidArgument:
            await self.bot.say("You're not in a VC .-.")
            return
        except discord.ClientException:
            pass
        try:
            self.voice[ctx.message.server.id][1].stop()
            self.voice[ctx.message.server.id][1] = None
        except:
            pass

        if 'youtube.com' in searchTerm.lower() or 'youtu.be' in searchTerm.lower():
            pass
        else:
            searchTerm = 'ytsearch:' + searchTerm

        self.voice[ctx.message.server.id][1] = await self.voice[ctx.message.server.id][0].create_ytdl_player(searchTerm)
        self.voice[ctx.message.server.id][1].start()
        self.voice[ctx.message.server.id][1].volume = 0.2
        lenth = str(datetime.timedelta(seconds=self.voice[ctx.message.server.id][1].duration))
        await self.bot.say("Now playing :: `{0.title}` :: `[{1}]`".format(self.voice[ctx.message.server.id][1], lenth))


    @commands.command(pass_context=True)
    async def join(self, ctx):
        try:
            self.voice[ctx.message.server.id][0] = await self.bot.join_voice_channel(ctx.message.author.voice_channel)
        except discord.InvalidArgument:
            await self.bot.say("You're not in a VC .-.")
            return
        except discord.ClientException:
            await self.bot.say("I-I'm already here though... ;-;")
            return
        await self.bot.say("Joined ya~")


    @commands.command(pass_context=True)
    async def leave(self, ctx):
        try:
            await self.voice[ctx.message.server.id][0].disconnect()
            self.voice[ctx.message.server.id][0] = None
            await self.bot.say("Okay bye :c")
        except:
            await self.bot.say("But I'm not there anyway? I'm sorry you want me gone so much, but like... chill.")


    @commands.command(pass_context=True,aliases=['p','P','PLAY'])
    async def play(self, ctx):
        await self.musicMan(ctx, ctx.message.content.split(' ',1)[1])


    @commands.command(pass_context=True, aliases=['syop'])
    async def stop(self, ctx):
        if self.voice[ctx.message.server.id][1] == None:
            await self.bot.say("I'm not playing anything but okay whatever")
            return
        self.voice[ctx.message.server.id][1].stop()
        self.voice[ctx.message.server.id][1] = None 
        # self.voice[ctx.message.server.id][2] = None
        # self.voice[ctx.message.server.id][3] = []
        await self.bot.say("k done")


    @commands.command(pass_context=True,hidden=True)
    async def scream(self, ctx):
        await self.musicMan(ctx, "incoherent screaming")


    @commands.command(pass_context=True,hidden=True)
    async def fuckmyass(self, ctx):
        await self.musicMan(ctx, "mujsPpzx2Sc")


    @commands.command(pass_context=True,hidden=True)
    async def rickroll(self, ctx):
        await self.musicMan(ctx, "dQw4w9WgXcQ")


    @commands.command(pass_context=True,hidden=True)
    async def badopinion(self, ctx):
        await self.musicMan(ctx, "hitler did nothing wrong")


    @commands.command(pass_context=True,hidden=True)
    async def soviet(self, ctx):
        await self.musicMan(ctx, "U06jlgpMtQs")


    @commands.command(pass_context=True,hidden=True)
    async def wet(self, ctx):
        await self.musicMan(ctx, "Hit me with your wet dick")


    @commands.command(pass_context=True,hidden=True)
    async def stfu(self, ctx):
        await self.musicMan(ctx, "OLpeX4RRo28") 


    @commands.command(pass_context=True,hidden=True)
    async def kim(self, ctx):
        await self.musicMan(ctx, "kim possible theme")


    @commands.command(pass_context=True,hidden=True)
    async def flute(self, ctx):
        toPlay = random.choice(['nF7lv1gfP1Q','2IRcM9qwDwo','Qh6z8qOaXro','VeFzYPKbz1g','GUhVe4DHN98','a-P0p_UtagM'])
        await self.musicMan(ctx, toPlay)


    @commands.command(pass_context=True,hidden=True)
    async def putin(self, ctx):
        await self.musicMan(ctx, "PUTIN IS NUMBER ONE GREATEST PRESIDENT SONG")


    @commands.command(pass_context=True,hidden=True)
    async def bike(self, ctx):
        await self.musicMan(ctx, "nigger stole my bike")


    @commands.command(pass_context=True)
    async def pause(self, ctx):
        if self.voice[ctx.message.server.id][0] == None:
            await self.bot.say("I'm can't pause if I'm not playing anything u lil shit.")
            return
        if self.voice[ctx.message.server.id][1] == None:
            await self.bot.say("I'm can't pause if I'm not playing anything u lil shit.")
            return
        self.voice[ctx.message.server.id][1].pause()
        await self.bot.say('kdun')


    @commands.command(pass_context=True)
    async def resume(self, ctx):
        if self.voice[ctx.message.server.id][0] == None:
            await self.bot.say("I'm can't resume if I'm not playing anything u lil shit.")
            return
        if self.voice[ctx.message.server.id][1] == None:
            await self.bot.say("I'm can't resume if I'm not playing anything u lil shit.")
            return
        self.voice[ctx.message.server.id][1].resume()
        await self.bot.say('kden')


    @commands.command(pass_context=True,aliases=['vol','v'])
    async def volume(self, ctx):
        if self.voice[ctx.message.server.id][1] == None:
            await self.bot.say("I aint playin anythin m8")
            return
        toVol = float(ctx.message.content.split(' ')[1])
        maxVol = 100
        if toVol > maxVol:
            toVol = maxVol
        if toVol < 0: 
            toVol = 0
        self.voice[ctx.message.server.id][1].volume = toVol/100
        await self.bot.say("Volume changed to {}%".format(toVol))


    @commands.command(pass_context=True,aliases=[])
    async def np(self, ctx):
        if self.voice[ctx.message.server.id][1] == None:
            await self.bot.say("You are `1/{}` of the way through your life".format(random.randint(2,15)))
            return
        lenth = str(datetime.timedelta(seconds=self.voice[ctx.message.server.id][1].duration))
        await self.bot.say("Now playing :: `{0.title}` :: `[{1}]`".format(self.voice[ctx.message.server.id][1], lenth))



def setup(bot):
    bot.add_cog(Voice(bot))
