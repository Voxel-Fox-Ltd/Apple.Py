import discord
from discord.ext import commands
import json
import os
import sys
from isAllowed import *


workingDirectory = os.path.dirname(os.path.realpath(__file__)) + \
    "\\botTxtFiles\\"
serverConfigs = os.path.dirname(os.path.realpath(__file__)) + \
    "\\botTxtFiles\\serverConfigs\\"


notallowed = "You are not allowed to use that command."
waitmessage = "Please wait..."


class CustomCommands():

    def __init__(self, bot):
        self.bot = bot

    @commands.group(pass_context=True)
    async def cc(self, ctx):
        pass

    @cc.command(name='add', pass_context=True, description='Adds a custom command to the server.')
    async def ccadd(self, ctx):
        toWrite = None
        try:
            with open(serverConfigs + ctx.message.server.id + '.json') as a:
                toWrite = json.load(a)
        except FileNotFoundError:
            with open(serverConfigs + ctx.message.server.id + '.json', 'w') as a:
                toWrite = {"Commands": {}, "Channels": {
                    "Bans": "", "RSS": {}}, "CustomCommands": {}}
                a.write(json.dumps(toWrite, indent=4))

        try:
            commThread = toWrite['CustomCommands']
            if len(commThread) >= 20:
                await self.bot.say("Hey, you already have 20 commands. You don't need any more  <3")
                return
        except KeyError:
            commThread = toWrite['CustomCommands'] = {}

        z = ctx.message.content
        commandToAdd = z.split(' ', 3)[2].lower()
        commandToEval = z.split(' ', 3)[3]
        # try:
        #     q = eval(commandToEval)
        # except Exception as e:
        #     await self.bot.say("This command does not evaluate a Python expression\n\n```%s```" %str(repr(e)))
        #     return
        commThread[commandToAdd] = commandToEval

        toWrite['CustomCommands'] = commThread
        toFile = json.dumps(toWrite, indent=4)

        with open(serverConfigs + ctx.message.server.id + '.json', 'w') as data_file:
            data_file.write(toFile)

        await self.bot.say("Command added.")

    @cc.command(name='delete', aliases=['del', 'rem', 'remove'], pass_context=True, description='Removes a custom command from the server.')
    async def ccdel(self, ctx):
        toWrite = None
        try:
            with open(serverConfigs + ctx.message.server.id + '.json') as a:
                toWrite = json.load(a)
        except FileNotFoundError:
            with open(serverConfigs + ctx.message.server.id + '.json', 'w') as a:
                toWrite = {"Commands": {}, "Channels": {
                    "Bans": "", "RSS": {}}, "CustomCommands": {}}
                a.write(json.dumps(toWrite, indent=4))
                await self.bot.say("That command isn't defined.")
                return

        commThread = toWrite['CustomCommands']

        z = ctx.message.content
        commandToDel = z.split(' ')[2]
        try:
            del commThread[commandToDel]
        except KeyError:
            await self.bot.say("That command isn't defined.")
            return

        toWrite['CustomCommands'] = commThread
        toFile = json.dumps(toWrite, indent=4)

        with open(serverConfigs + ctx.message.server.id + '.json', 'w') as data_file:
            data_file.write(toFile)

        await self.bot.say("Command deleted.")

    @cc.command(name='list', pass_context=True, description='Lists all of the custom commands that the server can use.')
    async def cclist(self, ctx):
        with open(serverConfigs + ctx.message.server.id + '.json') as data_file:
            customCommands = json.load(data_file)

        try:
            comms = customCommands['CustomCommands']
        except KeyError:
            await self.bot.say("There are no set custom commands for this server.")
            return

        if comms == {}:
            await self.bot.say("There are no set custom commands for this server.")
            return

        x = ''
        for i in comms:
            x = x + '* ' + i + '\n'

        await self.bot.send_message(ctx.message.author, "These are the commands for that server:\n```%s```" % x)


def setup(bot):
    bot.add_cog(CustomCommands(bot))
