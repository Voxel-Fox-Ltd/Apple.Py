import discord
from discord.ext import commands
import json
import os
import sys
from isAllowed import *


notallowed = "You are not allowed to use that command."
waitmessage = "Please wait..."


def normalize(toNormal):
    toNormal = toNormal.message.content.split(' ')[2].lower()
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
        if allowUse(ctx) == False:
            await self.bot.say("You have to be an admin to use this command.")
        else ctx.invoked_subcommand is None:
            await self.bot.say("Please use `config help` to see how to use this command properly.")


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
        currentAllow[toEnable]['Enabled'] = 'True'
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
        currentAllow[toEnable]['Enabled'] = 'False'
        writeAllow(ctx,currentAllow)
        await self.bot.say("Configs updated.")


    @config.command(name='set',pass_context=True)
    async def configSet(self, ctx):
        try:
            toEnable = normalize(ctx)
            if toEnable == 'ImgurAlbum':
                raise IOError("The input from the user was not found in the configuration JSON.")
        except IOError as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            await self.bot.say("Something went wrong :: {}".format(exc))

        try:
            toSet = ctx.message.raw_channel_mentions[0]
        except IndexError as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            await self.bot.say("Something went wrong :: {}".format(exc))

        currentAllow = giveAllowances(ctx)
        currentAllow[toEnable]['Channel'] = str(toSet)
        writeAllow(ctx,currentAllow)
        await self.bot.say("Configs updated.")


def setup(bot):
    bot.add_cog(Permissions(bot))
