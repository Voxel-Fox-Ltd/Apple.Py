from isAllowed import *


class Voice():


    def __init__(self, bot):
        self.bot = bot
        self.voice = {}

        # Start OPUS if not loaded
        if not discord.opus.is_loaded():
            discord.opus.load_opus()

        # Load what VCs it's already in
        for i in self.bot.servers:
            # [VoiceClient, StreamClient, Volume, LastCalled, QueuedSearchTerms]
            self.voice[i.id] = [self.bot.voice_client_in(i), None, 0.2, 0.0, []]


    async def musicMan(self, ctx, searchTerm=None):

        try:
            await self.bot.add_reaction(ctx.message, '👀')
        except:
            # I don't need t a wait message here tbh
            pass

        if time.time() > self.voice[ctx.message.server.id][3] + 5:
            self.voice[ctx.message.server.id][3] = time.time()
        else:
            await self.bot.say("Please wait 5 seconds between songs before calling another.")
            return

        with open(workingDirectory+"\\moobotBlacklist.txt") as a:
            q = a.read()
            blacklistedUsers = q.split('\n')

        if ctx.message.author.id in blacklistedUsers:
            await self.bot.say("Sorry but you've been blacklisted.")
            return

        # Attempt to join the calling user's VC
        try:
            self.voice[ctx.message.server.id][0] = await self.bot.join_voice_channel(ctx.message.author.voice_channel)
        except discord.InvalidArgument:
            await self.bot.say("You're not in a VC .-.")
            return
        except discord.ClientException:
            pass

        # Stop any playing music currently if there is any
        try:
            self.voice[ctx.message.server.id][1].stop()
            self.voice[ctx.message.server.id][1] = None
        except:
            pass

        # Differentiate between search terms and other
        if "youtube.com" in searchTerm.lower():
            searchTerm = searchTerm.split('?v=')[1][:11]
        searchTerm = 'ytsearch:' + searchTerm

        # Create StreamClient
        try:
            self.voice[ctx.message.server.id][1] = await self.voice[ctx.message.server.id][0].create_ytdl_player(searchTerm)
            self.voice[ctx.message.server.id][1].start()
            self.voice[ctx.message.server.id][1].volume = self.voice[ctx.message.server.id][2]
        except:
            await self.bot.say("There were no video results for that/the video was disabled for non-YouTube playback.")
            self.voice[ctx.message.server.id][1] = None
            return

        # Blacklist earrape
        title = self.voice[ctx.message.server.id][1].title.lower()
        for i in ['earrape','ear rape','rip headphone','ripheadphone','Thomas the Pain Train']:
            if i.lower() in title:
                await self.bot.say("Pls no earrape thx")
                self.voice[ctx.message.server.id][1].stop()
                self.voice[ctx.message.server.id][1] = None
                return
                
        for i in ['yee']:
            if i.lower() in title:
                await self.bot.say("No.")
                self.voice[ctx.message.server.id][1].stop()
                self.voice[ctx.message.server.id][1] = None
                return

        # Blacklist songs longer than 5 hours
        length = self.voice[ctx.message.server.id][1].duration
        if length > 60*60*5:
            await self.bot.say("This song is longer than 5 hours - stopping.")
            self.voice[ctx.message.server.id][1].stop()
            self.voice[ctx.message.server.id][1] = None
            return

        # Output to client
        lenth = str(datetime.timedelta(seconds=self.voice[ctx.message.server.id][1].duration))
        await self.bot.say("Now playing :: `{0.title}` :: `[{1}]`".format(self.voice[ctx.message.server.id][1], lenth))


    @commands.command(pass_context=True, aliases=['summon'])
    async def join(self, ctx):
        await self.joinNoCommand(ctx, True)


    async def joinNoCommand(self, ctx, outputToClient = False):

        with open(workingDirectory+"\\moobotBlacklist.txt") as a:
            q = a.read()
            blacklistedUsers = q.split('\n')
            
        if ctx.message.author.id in blacklistedUsers:
            await self.bot.say("Sorry but you've been blacklisted.")
            return

        # Attempt to join the calling user's VC
        try:
            self.voice[ctx.message.server.id][0] = await self.bot.join_voice_channel(ctx.message.author.voice_channel)
        except discord.InvalidArgument:
            if outputToClient: await self.bot.say("You're not in a VC .-.")
            return
        except discord.ClientException:
            if outputToClient: await self.bot.say("I-I'm already here though... ;-;")
            return
        if outputToClient: await self.bot.say("Joined ya~")


    @commands.command(pass_context=True)
    async def queue(self, ctx, *, searchTerm : str):
        pass


    @commands.command(pass_context=True)
    async def leave(self, ctx):

        with open(workingDirectory+"\\moobotBlacklist.txt") as a:
            q = a.read()
            blacklistedUsers = q.split('\n')
            
        if ctx.message.author.id in blacklistedUsers:
            await self.bot.say("Sorry but you've been blacklisted.")
            return

        # Attempt to disconnect from any joined VC in the server
        try:
            await self.voice[ctx.message.server.id][0].disconnect()
            self.voice[ctx.message.server.id][0] = None
            await self.bot.say("Okay bye :c")
        except:
            await self.bot.say("But I'm not there anyway? I'm sorry you want me gone so much, but like... chill.")


    @commands.command(pass_context=True, aliases=['syop','STOP','st0p','ST0P'])
    async def stop(self, ctx):
        await self.stopNoCommand(ctx, True)


    async def stopNoCommand(self, ctx, outputToClient = False):

        with open(workingDirectory+"\\moobotBlacklist.txt") as a:
            q = a.read()
            blacklistedUsers = q.split('\n')
            
        if ctx.message.author.id in blacklistedUsers:
            await self.bot.say("Sorry but you've been blacklisted.")
            return

        # Attempt to stop the currently playing StreamClient
        if self.voice[ctx.message.server.id][1] == None:
            if outputToClient: await self.bot.say("I'm not playing anything but okay whatever")
            return
        self.voice[ctx.message.server.id][1].stop()
        self.voice[ctx.message.server.id][1] = None 
        self.voice[ctx.message.server.id][4] = []
        if outputToClient: await self.bot.say("k done")


    @commands.command(pass_context=True,aliases=['p','P','PLAY'])
    async def play(self, ctx, *, searchTerm : str):
        await self.musicMan(ctx, searchTerm)


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
        fluteSongs = ['nF7lv1gfP1Q','2IRcM9qwDwo','Qh6z8qOaXro','VeFzYPKbz1g','GUhVe4DHN98','a-P0p_UtagM']
        toPlay = random.choice(fluteSongs)
        await self.musicMan(ctx, toPlay)


    @commands.command(pass_context=True,hidden=True)
    async def putin(self, ctx):
        await self.musicMan(ctx, "PUTIN IS NUMBER ONE GREATEST PRESIDENT SONG")


    @commands.command(pass_context=True,hidden=True)
    async def bike(self, ctx):
        await self.musicMan(ctx, "nigger stole my bike")


    # @commands.command(pass_context=True,hidden=True)
    # async def succ(self, ctx):
    #     await self.musicMan(ctx, "succ")


    @commands.command(pass_context=True,hidden=True)
    async def shia(self, ctx):
        await self.musicMan(ctx, "\"Shia LaBeouf\" Live - Rob Cantor")


    @commands.command(pass_context=True,hidden=True)
    async def sorry(self, ctx):
        await self.musicMan(ctx, "liberal democrats apology song autotune")


    @commands.command(pass_context=True,hidden=True)
    async def same(self, ctx):
        await self.musicMan(ctx, "Hey how you doing. Well I'm doing just fine. I lied I'm dying inside vine by Choonie")


    @commands.command(pass_context=True,hidden=True)
    async def spain(self, ctx):
        await self.musicMan(ctx, "9-_2QpbXMbw")


    @commands.command(pass_context=True)
    async def pause(self, ctx):

        with open(workingDirectory+"\\moobotBlacklist.txt") as a:
            q = a.read()
            blacklistedUsers = q.split('\n')
            
        if ctx.message.author.id in blacklistedUsers:
            await self.bot.say("Sorry but you've been blacklisted.")
            return

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

        with open(workingDirectory+"\\moobotBlacklist.txt") as a:
            q = a.read()
            blacklistedUsers = q.split('\n')
            
        if ctx.message.author.id in blacklistedUsers:
            await self.bot.say("Sorry but you've been blacklisted.")
            return

        if self.voice[ctx.message.server.id][0] == None:
            await self.bot.say("I'm can't resume if I'm not playing anything u lil shit.")
            return
        if self.voice[ctx.message.server.id][1] == None:
            await self.bot.say("I'm can't resume if I'm not playing anything u lil shit.")
            return
        self.voice[ctx.message.server.id][1].resume()
        await self.bot.say('kden')


    @commands.command(pass_context=True,aliases=['vol','v'])
    async def volume(self, ctx, toVol : str = '20'):

        with open(workingDirectory+"\\moobotBlacklist.txt") as a:
            q = a.read()
            blacklistedUsers = q.split('\n')
            
        if ctx.message.author.id in blacklistedUsers:
            await self.bot.say("Sorry but you've been blacklisted.")
            return
                    
        if self.voice[ctx.message.server.id][1] == None:
            await self.bot.say("I aint playin anythin m8")
            return
        toVol = float(toVol)
        maxVol = 100
        if toVol > maxVol:
            toVol = maxVol
        if toVol < 0: 
            toVol = 0
        self.voice[ctx.message.server.id][1].volume = toVol/100
        self.voice[ctx.message.server.id][2] = toVol/100
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
