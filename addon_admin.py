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
        """Kick command."""
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


    @emoji.command(pass_context=True,name='add',hidden=True)
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


    @commands.command(pass_context=True, help=helpText['pin'][1], brief=helpText['pin'][0])
    async def pin(self, ctx):
        """Pins the last message to the channel."""
        if allowUse(ctx, ['manage_messages']) == False:
            await self.bot.say(notallowed)
            return
        if len(ctx.message.content.split(' ')) == 1:
            async for i in self.bot.logs_from(ctx.message.channel, limit=2):
                message = i
        else:
            message = self.bot.get_message(
                ctx.message.channel, ctx.message.content.split(' ')[1])
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
    bot.add_cog(Admin(bot))
