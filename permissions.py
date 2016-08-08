import discord
from discord.ext import commands
import json
import os
import sys
from isAllowed import *


notallowed = "You are not allowed to use that command."
waitmessage = "Please wait..."


class Permissions():
    def __init__(self, bot):
        self.bot = bot

    @commands.group(pass_context=True)
    async def config(self, ctx):
        if not isAllowed(ctx, sys._getframe().f_code.co_name):
            await self.bot.say(notallowed)
            return

    @config.group(name='commands',pass_context=True)
    async def configCommands(self, ctx):
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


    @configCommands.command(name='add',pass_context=True)
    async def configCommandsAdd(self, ctx):
        toWrite = None 
        try:
            with open(serverConfigs+ctx.message.server.id+'.json') as a:
                toWrite = json.load(a)
        except FileNotFoundError:
            with open(serverConfigs+ctx.message.server.id+'.json', 'w') as a:
                toWrite = {"Commands":{},"Channels":{"Bans":""}}
                a.write(json.dumps(toWrite,indent=4))

        comToChange = ctx.message.content.split(' ')[3]

        try:
            curAllowed = toWrite['Commands'][comToChange]['CanUse']
        except KeyError:
            curAllowed = []
            try:
                toWrite['Commands'][comToChange]['CanUse'] = []
            except KeyError:
                toWrite['Commands'][comToChange] = {'CanUse':[]}

        try:
            for i in ctx.message.role_mentions:
                curAllowed.append(i.id)
        except:
            for i in ctx.message.server.roles:
                if i.name.lower() == ctx.message.content.split(' ',4)[4]:
                    curAllowed.append(i.id)
                    break
        toWrite['Commands'][comToChange]['CanUse'] = curAllowed

        with open(serverConfigs+ctx.message.server.id+'.json', 'w') as a:
            a.write(json.dumps(toWrite,indent=4))

        await self.bot.say("Roles added to approved userlist.")

    @configCommands.command(name='remove',pass_context=True)
    async def configCommandsRemove(self, ctx):
        toWrite = None 
        try:
            with open(serverConfigs+ctx.message.server.id+'.json') as a:
                toWrite = json.load(a)
        except FileNotFoundError:
            with open(serverConfigs+ctx.message.server.id+'.json', 'w') as a:
                toWrite = {"Commands":{},"Channels":{"Bans":""}}
                a.write(json.dumps(toWrite,indent=4))

        comToChange = ctx.message.content.split(' ')[3]

        try:
            curAllowed = toWrite['Commands'][comToChange]['CanUse']
        except KeyError:
            curAllowed = []
            try:
                toWrite['Commands'][comToChange]['CanUse'] = []
            except KeyError:
                toWrite['Commands'][comToChange] = {'CanUse':[]}

            with open(serverConfigs+ctx.message.server.id+'.json', 'w') as a:
                a.write(json.dumps(toWrite,indent=4))

            await self.bot.say("Roles removed from approved userlist.")
            return

        for i in ctx.message.role_mentions:
            while i.id in curAllowed:
                curAllowed.remove(i.id)
        toWrite['Commands'][comToChange]['CanUse'] = curAllowed

        with open(serverConfigs+ctx.message.server.id+'.json', 'w') as a:
            a.write(json.dumps(toWrite,indent=4))

        await self.bot.say("Roles removed from approved userlist.")

def setup(bot):
    bot.add_cog(Permissions(bot))