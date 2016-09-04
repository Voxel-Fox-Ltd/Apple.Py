import discord
from discord.ext import commands
import json
import os
import sys
from isAllowed import *


notallowed = "You are not allowed to use that command."
waitmessage = "Please wait..."


class Counting():

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def usrcount(self, ctx):
        try:
            toCount = ctx.message.content.split(' ', 1)[1].lower()
        except IndexError:
            count = 0
            for i in ctx.message.server.members:
                count += 1
            await self.bot.say("There are **{}** users on this server.".format(count))
            return
        count = 0
        usersOnServer = 0
        for i in ctx.message.server.members:
            if toCount in i.display_name.lower():
                count += 1
            usersOnServer += 1
        dp = 2
        while True:
            percentUsers = format((count / usersOnServer) * 100, '.%sf' % dp)
            if percentUsers[-1] == '0':
                dp += 1
            else:
                break
            if dp >= 10:
                break
        await self.bot.say("There are **%s** users with '%s' in their display name on this server. That makes up **%s** percent of users on the server." % (str(count), toCount, percentUsers))

    @commands.command(pass_context=True)
    async def gamecount(self, ctx):
        toCount = ctx.message.content.split(' ', 1)[1].lower()
        count = 0
        usersOnServer = 0
        for i in ctx.message.server.members:
            try:
                if toCount in i.game.name.lower():
                    count += 1
            except AttributeError:
                pass
            usersOnServer += 1
        dp = 2
        while True:
            percentUsers = format((count / usersOnServer) * 100, '.%sf' % dp)
            if percentUsers[-1] == '0':
                dp += 1
            else:
                break
            if dp >= 10:
                break
        await self.bot.say("There are **%s** users playing '%s' on this server. That makes up %s percent of users on the server." % (str(count), toCount, percentUsers))


def setup(bot):
    bot.add_cog(Counting(bot))
