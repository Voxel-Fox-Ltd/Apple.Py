import discord
from discord.ext import commands
import json
import os
import sys
from isAllowed import *


notallowed = "You are not allowed to use that command."
waitmessage = "Please wait..."


def normalize(toNormal):
    toNormal = toNormal.message.content.split(' ',3)[3].lower()
    if toNormal in ['bans','ban']: toNormal = 'Bans'
    elif toNormal in ['joins','enter','entry','join']: toNormal = 'Joins'
    elif toNormal in ['leaves','leave','disconnect']: toNormal = 'Leaves'
    elif toNormal in ['imgur','album','imgur album']: toNormal = 'ImgurAlbum'
    else:
        raise IOError("The input from the user was not found in the configuration JSON.")

    return toNormal

class Permissions():
    def __init__(self, bot):
        self.bot = bot


    @commands.group(pass_context=True)
    async def config(self, ctx):
        pass


    @config.command(name='byname',pass_context=True)
    async def configSelf(self, ctx):
        toConfig = ctx.message.content.split(' ',2)[2].split(' ')
        i = giveAllowances(ctx)
        if len(toConfig) == 4:
            i[toConfig[0]][toConfig[1]][toConfig[2]] = toConfig[3]
        elif len(toConfig) == 3:
            i[toConfig[0]][toConfig[1]] = toConfig[2]
        else:
            await self.bot.say("Someone fucked up somewhere.")
            return
        writeAllow(ctx,i)
        await self.bot.say("Configs updated.")


    @config.command(name='enable',pass_context=True)
    async def configEnable(self, ctx):
        try:
            toEnable = normalize(ctx)
        except IOError as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            await self.bot.say("Something went wrong :: {}".format(exc))
        currentAllow = giveAllowances(ctx)
        currentAllow[toEnable] = 'True'
        writeAllow(ctx,currentAllow)
        await self.bot.say("Configs updated.")

    @config.command(name='disable',pass_context=True)
    async def configDisable(self, ctx):
        try:
            toEnable = normalize(ctx)
        except IOError as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            await self.bot.say("Something went wrong :: {}".format(exc))
        currentAllow = giveAllowances(ctx)
        currentAllow['toEnable'] = 'False'
        writeAllow(ctx,currentAllow)
        await self.bot.say("Configs updated.")



def setup(bot):
    bot.add_cog(Permissions(bot))
