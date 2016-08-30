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

class Configuration():
    def __init__(self, bot):
        self.bot = bot


    @commands.group(pass_context=True,help=helpText['config'])
    async def config(self, ctx):
        """Parent command for config."""
        if allowUse(ctx) == False:
            await self.bot.say(notallowed)
            return
        elif ctx.invoked_subcommand is None:
            await self.bot.say("Please use `config help` to see how to use this command properly.")


    @config.command(name='enable',pass_context=True)
    async def configEnable(self, ctx):
        if allowUse(ctx) == False: return
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
        if allowUse(ctx) == False: return
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
        if allowUse(ctx) == False: return
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


    @commands.group(pass_context=True,help=helpText['channel'])
    async def channel(self, ctx):
        """Parent command for channel."""
        if allowUse(ctx, ['manage_channels']) == False: 
            await self.bot.say(notallowed)
            return
        elif ctx.invoked_subcommand is None:
            await self.bot.say("Please use `channel help` to see how to use this command properly.")


    @channel.command(name='create',aliases=['add','make'],pass_context=True)    
    async def channelCreate(self, ctx):
        if allowUse(ctx, ['manage_channels']) == False: return
        serverObj = ctx.message.server 
        channelName = ctx.message.content.split(' ',2)[2]
        try:
            await self.bot.create_channel(serverObj, channelName)
            await self.bot.say("Channel created.")
        except Exception as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            await self.bot.say("Something went wrong :: {}".format(exc))


    @channel.command(name='delete',aliases=['del','remove','rem','rm'],pass_context=True)
    async def channelDelete(self, ctx):
        if allowUse(ctx, ['manage_channels']) == False: return
        try:
            toSet = ctx.message.raw_channel_mentions[0]
        except IndexError as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            await self.bot.say("Something went wrong :: {}".format(exc))
            return

        try:
            await self.bot.delete_channel(discord.Object(toSet))
            await self.bot.say("Channel deleted.")
        except Exception as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            await self.bot.say("Something went wrong :: {}".format(exc))
            return


    @commands.command(pass_context=True)
    async def pin(self, ctx):
        """Pins the last message to the channel."""
        if allowUse(ctx, ['manage_messages']) == False:
            await self.bot.say(notallowed)
            return
        if len(ctx.message.content.split(' ')) == 1:
            async for i in self.bot.logs_from(ctx.message.channel, limit=2):
                message = i 
        else:
            message = self.bot.get_message(ctx.message.channel, ctx.message.content.split(' ')[1])
            # message = discord.Object(ctx.message.content.split(' ')[1])
            await self.bot.say(ctx.message.content.split(' ')[1])
            await self.bot.say(type(message))
        try:
            await self.bot.pin_message(message)
        except discord.HTTPException as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            await self.bot.say("Something went wrong :: {}\nIt's likely that there are 50 pins in this channel already - that's the limit for Discord.".format(exc))
        except Exception as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            await self.bot.say("Something went wrong :: {}".format(exc))



def setup(bot):
    bot.add_cog(Configuration(bot))
