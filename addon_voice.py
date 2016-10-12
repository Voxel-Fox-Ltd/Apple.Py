from isAllowed import *


class Voice():


    def __init__(self, bot):
        self.bot = bot
        self.voice = {}
        if not discord.opus.is_loaded():
            discord.opus.load_opus()
        for i in self.bot.servers:
            self.voice[i.id] = [self.bot.voice_client_in(i), None, []]


    async def musicMan(self, ctx, searchTerm):
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
        self.voice[ctx.message.server.id][1] = await self.voice[ctx.message.server.id][0].create_ytdl_player('ytsearch:'+searchTerm)
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
        if self.voice[ctx.message.server.id]:
            await self.voice[ctx.message.server.id][0].disconnect()
            self.voice[ctx.message.server.id][0] = None
            await self.bot.say("Okay bye :c")
        else:
            await self.bot.say("But I'm not there anyway? I'm sorry you want me gone so much, but like... chill.")


    @commands.command(pass_context=True)
    async def play(self, ctx):
        await self.musicMan(ctx, ctx.message.content.split(' ',1)[1])


    @commands.command(pass_context=True, aliases=['syop'])
    async def stop(self, ctx):
        if self.voice[ctx.message.server.id][1] == None:
            await self.bot.say("I'm not playing anything but okay whatever")
            return
        self.voice[ctx.message.server.id][1].stop()
        self.voice[ctx.message.server.id][1] = None 
        await self.bot.say("k done")


    @commands.command(pass_context=True)
    async def scream(self, ctx):
        await self.musicMan(ctx, "incoherent screaming")


    @commands.command(pass_context=True)
    async def fuckmyass(self, ctx):
        await self.musicMan(ctx, "mujsPpzx2Sc")


    @commands.command(pass_context=True)
    async def rickroll(self, ctx):
        await self.musicMan(ctx, "dQw4w9WgXcQ")


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


    @commands.command(pass_context=True)
    async def volume(self, ctx):
        if self.voice[ctx.message.server.id][1] == None:
            await self.bot.say("I aint playin anythin m8")
            return
        toVol = int(ctx.message.content.split(' ')[1])
        if toVol > 200:
            toVol = 200
        if toVol < 0: 
            toVol = 0
        self.voice[ctx.message.server.id][1].volume = toVol/100
        await self.bot.say("Volume changed to {}%".format(toVol))



def setup(bot):
    bot.add_cog(Voice(bot))
