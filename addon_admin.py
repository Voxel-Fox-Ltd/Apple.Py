import discord
from discord.ext import commands
import json
import os
import sys
import strawpoll
from isAllowed import *
from urllib.request import urlretrieve


notallowed = "You are not allowed to use that command."
waitmessage = "Please wait..."


api = strawpoll.API()


class Admin():

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
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

    @commands.command(pass_context=True)
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


    @commands.group(pass_context=True)
    async def emoji(self, ctx):
        """Parent command for emoji usage"""
        pass


    @emoji.command(pass_context=True,name='add')
    async def emojiAdd(self, ctx):
        if allowUse(ctx, ['emoji']):
            emojiName = ctx.message.content.split(' ',3)[2]
            imgUrl = ctx.message.content.split(' ',3)[3]
            urlretrieve(imgUrl, 'emojiTEMP.png')
            a = open('emojiTEMP.png', 'rb')
            b = a.read()
            a.close()
            await self.bot.create_custom_emoji(server=ctx.message.server, name=emojiName, image=b)
            await self.bot.say("This emoji has been added.")
        else:
            await self.bot.say(notallowed)


def setup(bot):
    bot.add_cog(Admin(bot))
