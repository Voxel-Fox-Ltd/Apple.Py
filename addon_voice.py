from isAllowed import *


class Voice():


    def __init__(self, bot):
        self.bot = bot
        self.voice = {}
        if not discord.opus.is_loaded():
            discord.opus.load_opus()
        for i in self.bot.servers:
            self.voice[i.id] = [None, None, []]
            try:
                self.bot.voice_client_in(i).disconnect()
            except:
                pass



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
    async def play(self, ctx, *, url:str):
        try:
            self.voice[ctx.message.server.id][1].stop()
        except:
            pass
        try:
            self.voice[ctx.message.server.id][0] = await self.bot.join_voice_channel(ctx.message.author.voice_channel)
        except discord.InvalidArgument:
            await self.bot.say("You're not in a VC .-.")
            return
        except discord.ClientException:
            pass
        self.voice[ctx.message.server.id][1] = await self.voice[ctx.message.server.id][0].create_ytdl_player('ytsearch:'+url)
        self.voice[ctx.message.server.id][1].start()
        m, s = divmod(self.voice[ctx.message.server.id][1].duration, 60)
        m = str(m)
        s = str(s)
        if len(str(s)) < 2:
            s = '0' + s
        await self.bot.say("Now playing :: `{0.title}` :: `[{1}:{2}]`".format(self.voice[ctx.message.server.id][1], m, s))


    @commands.command(pass_context=True)
    async def stop(self, ctx):
        if self.voice[ctx.message.server.id][1] == None:
            await self.bot.say("I'm not playing anything but okay whatever")
            return
        self.voice[ctx.message.server.id][1].stop()
        self.voice[ctx.message.server.id][1] = None 
        await self.bot.say("k done")



def setup(bot):
    bot.add_cog(Voice(bot))
