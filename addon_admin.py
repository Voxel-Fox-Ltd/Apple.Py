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


class Admin():

    def __init__(self, bot):
        self.bot = bot

    @commands.group(pass_context=True)
    async def ban(self, ctx):
        """Ban command."""
        if allowUse(ctx, ['ban']) == False:
            await self.bot.say(notallowed)
            return
        await self.bot.say("**{}** has been banned.".format(ctx.message.mentions[0]))
        i = giveAllowances(ctx)
        if i['Bans']['Channel'] != '':
            server = discord.Object(i['Bans']['Channel'])
            await self.bot.send_message(server, "**{}** has been banned.".format(ctx.message.mentions[0]))
        await self.bot.ban(ctx.message.mentions[0])


    @commands.group(pass_context=True)
    async def kick(self, ctx):
        """Ban command."""
        if allowUse(ctx, ['kick']) == False:
            await self.bot.say(notallowed)
            return
        await self.bot.say("**{}** has been kicked.".format(ctx.message.mentions[0]))
        i = giveAllowances(ctx)
        if i['Bans']['Channel'] != '':
            server = discord.Object(i['Bans']['Channel'])
            await self.bot.send_message(server, "**{}** has been kicked.".format(ctx.message.mentions[0]))
        await self.bot.kick(ctx.message.mentions[0])


def setup(bot):
    bot.add_cog(Admin(bot))
