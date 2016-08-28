import discord
from discord.ext import commands
import json
import os
import sys
import strawpoll
from isAllowed import *


notallowed = "You are not allowed to use that command."
waitmessage = "Please wait..."


api = strawpoll.API()


class Strawpoll():
    def __init__(self, bot):
        self.bot = bot


    @commands.group()
    async def strawpoll(self):
        pass 


    @strawpoll.command(pass_context=True,aliases=['push','make'])
    async def post(self, ctx):
        raw = ctx.message.content.split(' ',2)[2]
        nameStuff = raw.split('\n')
        nameOf = nameStuff[0]
        toMulti = False
        if nameStuff[-1].lower() in ['true','false','multi']:
            toMulti = {'true':True,'false':False,'multi':True}\
                      [nameStuff[-1].lower()]
            del(nameStuff[-1])
        del(nameStuff[0])
        tick = 0
        while True:
            try:
                toSub = strawpoll.Poll(nameOf, nameStuff, multi=toMulti)
                break 
            except TypeError:
                tick += 1
                if tick == 4:
                    await self.bot.say("The bot broke.")
                    return
                    
        await api.submit_poll(toSub)
        await self.bot.say('<%s>' %toSub.url)


    @strawpoll.command(pass_context=True,aliases=['get','results'])
    async def pull(self, ctx):
        raw = ctx.message.content.split(' ',2)[2]
        # idPost = raw.split('http://www.strawpoll.me/')[0][0:8]
        # await self.bot.say(idPost)
        results = await api.get_poll(raw)
        await self.bot.say(results.results())


def setup(bot):
    bot.add_cog(Strawpoll(bot))