import discord
from discord.ext import commands
import json
import os
import sys
from isAllowed import *


def normalize(toNormal):
    toNormal = toNormal.message.content.split(' ')[2].lower()
    if toNormal in ['bans', 'ban']:
        toNormal = 'Bans'
    elif toNormal in ['joins', 'enter', 'entry', 'join']:
        toNormal = 'Joins'
    elif toNormal in ['leaves', 'leave', 'disconnect']:
        toNormal = 'Leaves'
    elif toNormal in ['imgur', 'album', 'imgur album']:
        toNormal = 'ImgurAlbum'
    else:
        raise IOError(
            "The input from the user was not found in the configuration JSON.")

    return toNormal


class Configuration():

    def __init__(self, bot):
        self.bot = bot

    @commands.group(pass_context=True, help=helpText['config'][1], brief=helpText['config'][0])
    async def config(self, ctx):
        """Parent command for config."""
        if allowUse(ctx) == False:
            await self.bot.say(notallowed)
            return
        elif ctx.invoked_subcommand is None:
            await self.bot.say("Please use `config help` to see how to use this command properly.")

    @config.command(name='enable', pass_context=True)
    async def configEnable(self, ctx):
        if allowUse(ctx) == False:
            return
        try:
            toEnable = normalize(ctx)
        except IOError as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            await self.bot.say("Something went wrong :: {}".format(exc))
        currentAllow = giveAllowances(ctx)
        currentAllow[toEnable]['Enabled'] = 'True'
        writeAllow(ctx, currentAllow)
        await self.bot.say("Configs updated.")

    @config.command(name='disable', pass_context=True)
    async def configDisable(self, ctx):
        if allowUse(ctx) == False:
            return
        try:
            toEnable = normalize(ctx)
        except IOError as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            await self.bot.say("Something went wrong :: {}".format(exc))
        currentAllow = giveAllowances(ctx)
        currentAllow[toEnable]['Enabled'] = 'False'
        writeAllow(ctx, currentAllow)
        await self.bot.say("Configs updated.")

    @config.command(name='set', pass_context=True)
    async def configSet(self, ctx):
        if allowUse(ctx) == False:
            return
        try:
            toEnable = normalize(ctx)
            if toEnable == 'ImgurAlbum':
                raise IOError(
                    "The input from the user was not found in the configuration JSON.")
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
        writeAllow(ctx, currentAllow)
        await self.bot.say("Configs updated.")

    @config.command(name='text', pass_context=True)
    async def configText(self, ctx, textstr:str):
        if allowUse(ctx) == False:
            return
        try:
            toEnable = normalize(ctx)
            if toEnable == 'ImgurAlbum':
                raise IOError(
                    "The input from the user was not found in the configuration JSON.")
        except IOError as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            await self.bot.say("Something went wrong :: {}".format(exc))

        currentAllow = giveAllowances(ctx)
        currentAllow[toEnable]['Text'] = ctx.message.content.split(' ',3)[3]
        writeAllow(ctx, currentAllow)
        await self.bot.say("Configs updated.")

    @commands.group(pass_context=True)
    async def twitch(self, ctx):
        if allowUse(ctx, ['manage_server']):
            pass
        else:
            await self.bot.say(notallowed)

    @twitch.command(pass_context=True,name='add')
    async def twitchAdd(self, ctx, channelID:str):
        if not allowUse(ctx, ['manage_server']):
            return
        i = giveAllowances(ctx)
        strm = i['Streams']['TwitchTV']
        if channelID.lower() in strm:
            await self.bot.say("This user has already been added to the streamer list for this server.")
            return
        strm[channelID.lower()] = "-1"
        i['Streams']['TwitchTV'] = strm
        writeAllow(ctx, i)
        await self.bot.say("This user has now been added to the streamer list for this server.")

    @twitch.command(pass_context=True,name='del',aliases=['delete','rem','remove'])
    async def twitchDel(self, ctx, channelID:str):
        if not allowUse(ctx, ['manage_server']):
            return
        i = giveAllowances(ctx)
        strm = i['Streams']['TwitchTV']
        if channelID.lower() not in strm:
            await self.bot.say("This user isn't in the streamer list for this server.")
            return
        del strm[channelID.lower()]
        i['Streams']['TwitchTV'] = strm
        writeAllow(ctx, i)
        await self.bot.say("This user has now been removed from the streamer list for this server.")

    @twitch.command(pass_context=True,name='set')
    async def twitchSet(self, ctx, channelID:str):
        if not allowUse(ctx, ['manage_server']):
            return
        i = giveAllowances(ctx)
        try:
            chan = ctx.message.raw_channel_mentions[0]
        except IndexError:
            await self.bot.say("Please provide a channel.")
            return
        i['Streams']['Channel'] = chan
        writeAllow(ctx, i)
        await self.bot.say("The stream announcements have now been set to <#{}>".format(chan))


def setup(bot):
    bot.add_cog(Configuration(bot))
