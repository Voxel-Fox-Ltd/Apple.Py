## Discordpy essentials
import discord
import asyncio
from discord.ext import commands
## Exclusively for use with the restart command
import os
## Use of custom commands
import json
## Use of uptime and restart
import datetime
## Use of permissions within isAllowed
import sys
## Logging, obviously
import logging
## Use of client specific variables and functions
from isAllowed import *
## Converting album images into lists of regular images
from imgurpython import ImgurClient


## Set up the start time for the restart command
startTime = datetime.datetime.now()


## Start up some logging for debugging
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='%sbot.log' %workingDirectory, encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


## Create the bot
description = '''This is my bot I like to make it do things.'''
bot = commands.Bot(command_prefix='.', description=description, pm_help=True)


## Create all of the tokens and keys
discordToken = tokens['Skybot']
mashapeKey = {"X-Mashape-Key":
              tokens['Mashape']}
htmlHead = {'Accept-Endoding': 'identity'}
BOT_CLIENT_ID = tokens['SkybotID']
imgurUsr = ImgurClient(tokens['ImgurClient'], tokens['ImgurSecret'])


## Make the bot more unicode-friendly
non_bmp_map = dict.fromkeys(range(0x10000, sys.maxunicode + 1), 0xfffd)


## Because they're referenced so much, they're variables
notallowed = "You are not allowed to use that command."
waitmessage = "Please wait..."


## This uses the imgur API to convert an album into a list of links
def imgurAlbumToItems(albumLink):
    if type(albumLink) == str:
        imgObj = imgurUsr.get_album_images(albumLink)
        ret = ''
        for i in imgObj:
            ret = ret + i.link + '\n'
        ret = ret[:-1]
    elif albumLink.is_album:
        imgObj = imgurUsr.get_album_images(albumLink.id)
        ret = ''
        for i in imgObj:
            ret = ret + i.link + '\n'
        ret = ret[:-1]
    else:
        ret = albumLink.link
    return ret


helpText['echo'] = \
"""The bot will echo back whatever the user says to.

If a channel is mentioned inside of what the bot is told to echo, it will attempt to post the message there, instead of in the same channel that the command was called from. 
If a channel mention is detected, the bot will cut off the first word of the echo string.
This is to make it so you can have the first word as the place to be posted to, but keep in mind that *ALL* channel mentions are detected.

Usage :: echo Hello World
      :: echo #general Hello World
      :: echo #general Check out #bot-testing"""
@bot.command(pass_context=True,description='Echos what the user says.',help=helpText['echo'])
async def echo(ctx):
    """Simply says back what the person says."""
    if isAllowed(ctx, sys._getframe().f_code.co_name):
        print("Echoing :: %s" % ctx.message.content.split(' ',1)[1])
        try:
            chan = discord.Object(ctx.message.raw_channel_mentions[0])
            a = ctx.message.content.split(' ',2)[2]
        except:
            chan = ctx.message.channel
            a = ctx.message.content.split(' ',1)[1]
        await bot.send_message(chan, a)
        return 
    else:
        await bot.say(notallowed)


helpText['invite'] = \
"""Calling this will make the bot print out the invite command, so you can add it to your own server.
All of the permissions needed for the bot are included in the invite link.

Usage :: invite"""
@bot.command(pass_context=True,description='Gives you an invte link for the bot.',help=helpText['invite'])
async def invite(ctx):
    """Gives the invite link for the bot."""
    if isAllowed(ctx, sys._getframe().f_code.co_name):
        print("Told someone the invite link.")
        q = "https://discordapp.com/oauth2/authorize?scope=bot&client_id=%s&permissions=0x1c016c10" \
               % BOT_CLIENT_ID
        await bot.say(q)
    else:
        await bot.say(notallowed)
    return


helpText['purge'] = \
"""This will remove the last x messages from the channel, with x being the number you input. 
The number has no limit, so be careful with how much you delete.
This command will only run if the user calling it has manage messages, or administrator.

Usage :: purge 50"""
@bot.command(pass_context=True,description='Removes x amount of messages from chat.',help=helpText['purge'])
async def purge(ctx):
    """Purges x messages from the channel."""
    # if isAllowed(ctx, sys._getframe().f_code.co_name):
    if givePerms(ctx).manage_messages or givePerms(ctx).administrator:
        try:
            a = int(ctx.message.content.split(" ")[1])
        except ValueError:
            await bot.say("Please provide a value.")
        print("Deleting %s messages." %a)
        await bot.purge_from(ctx.message.channel, limit=a)
        print("Comleted deleting.")
    else:
        await bot.say(notallowed)
    return


helpText['rename'] = \
"""This will change the name of the bot to whatever is put after the command call.
If no name is given, then the bot will remove any nickname that it has.
This command will only run is the user calling it has manage nicknames, or administrator.

Usage :: rename Apple.py
      :: rename"""
@bot.command(pass_context=True,description='Changes the nickname of the bot.',help=helpText['rename'])
async def rename(ctx):
    """Renames the bot."""
    # if isAllowed(ctx, sys._getframe().f_code.co_name):
    if ( givePerms(ctx).manage_nicknames or givePerms(ctx).administrator ):
        ser = ctx.message.server.get_member_named(bot.user.name)
        try:
            await bot.change_nickname(ser, ctx.message.content.split(' ',1)[1])
            x = "Changed name to '%s'." % ctx.message.content.split(' ',1)[1]
        except IndexError:
            await bot.change_nickname(ser, '')
            x = "Removed nickname."
        await bot.say(x)
        # print("Changed nickname :: %s" % ctx.message.content.split(' ',1)[1])
    else:
        await bot.say(notallowed)
    return


helpText['uptime'] = \
"""This will show the current uptime of the bot, along with some other stats about its running.
'Uptime' references the time since the bot's last restart, so if the bot was recently restarted, despite no lapse in bot activity, the timer will count from its last time coming online.

Usage :: uptime"""
@bot.command(pass_context=True,description='Checks the uptime of the server.',help=helpText['uptime'])
async def uptime(ctx):
    """Shows the uptime of the bot."""
    now = datetime.datetime.now()
    up = now - startTime

    up = int(up.total_seconds())
    hours = up // 3600
    up -= hours * 3600
    minutes = up // 60
    up -= minutes * 60

    out = '''```%s hours
%s minutes
%s seconds```''' %(hours, minutes, up)

    userCount = []
    for i in bot.servers:
        for o in i.members:
            if o not in userCount:
                userCount.append(o)

    outplut = '''```On %s servers
Serving %s unique users```''' %(len(bot.servers),len(userCount))

    superOut = outplut + '\n' + out

    if isAllowed(ctx, sys._getframe().f_code.co_name):
        await bot.say(superOut)
    else:
        await bot.say(notallowed)
    return


helpText['ccolour'] = \
"""This will change the colour of the calling user.
The colour changed to is given by the user in the form of a hex code, and is done via roles.
In short, the bot checks if there is a role with the user's name and discriminator. If there is, the bot changes the colour of that role.
If there isn't, the bot creates one, assigns it to the user, tries to move it as far up as it can, and changes its colour.

Usage :: ccolour #FFFFFF
      :: ccolor FFFFFF"""
@bot.command(pass_context=True,description='Changes the colour of the submitter to a hex code.',aliases=['ccolor'],help=helpText['ccolour'])
async def ccolour(ctx):
    """Changes the users colour to the mentioned hex code."""
    if isAllowed(ctx, sys._getframe().f_code.co_name):
        flag = False
        try:
            hexc = ctx.message.content.split(' ')[1]
        except IndexError:
            await bot.say("Please provide a hex colour value.")
            return

        if hexc[0] == '#':
            hexc = hexc[1:]
        if len(hexc) != 6:
            await bot.say("Please provide a **hex** colour value.")
            return

        try:
            for role in ctx.message.server.roles:
                if str(role.name) == str(ctx.message.author):
                    await bot.edit_role(ctx.message.server, role, colour=discord.Colour(int(hexc, 16)))
                    rrr = role
                    print("Editing role :: %s" % str(role.name))
                    flag = True
            if flag == False:
                print("Creating role :: %s" % str(ctx.message.author))
                rrr = await bot.create_role(ctx.message.server, name=str(ctx.message.author), colour=discord.Colour(int(hexc, 16)))
                for i in range(0,500,1):
                    try:
                        await bot.move_role(ctx.message.server, rrr, i)
                        break
                    except discord.errors.InvalidArgument:
                        pass
                    except discord.ext.commands.errors.CommandInvokeError:
                        pass
            print("Adding role to user.")
            await bot.add_roles(ctx.message.author, rrr)
            await bot.say("Changed user role colour.")
        except discord.errors.Forbidden:
            await bot.say("This bot does not have permissions to manage roles.")
        return
    else:
        await bot.say(notallowed)


@bot.command(pass_context=True,description='Restarts the bot.',hidden=True)
async def restart(ctx):
    if ctx.message.author.id == '141231597155385344':

        with open(workingDirectory+'restartFile.txt','w') as a:
            a.write(str(ctx.message.channel.id))
        await bot.say("Restarting...")

        os.execl(sys.executable, *([sys.executable]+sys.argv))
    else:
        await bot.say('You have to be the bot\'s creator to use this command.')
    return


@bot.command(pass_context=True,description='Kills the bot.',hidden=True)
async def kill(ctx):
    if ctx.message.author.id == '141231597155385344':
        await bot.say("Killing.")
        sys.exit()
    else:
        await bot.say('You have to be the bot\'s creator to use this command.')
    return


@bot.event
async def on_member_join(member):
    server = member.server
    fmt = '**{0.mention}** hi welcome i love you.'
    i = giveAllowances(server)
    if i['Channels']['Joins']['Enabled'] == 'True':
        if i['Channels']['Joins']['Channel'] == '':
            await bot.send_message(server, fmt.format(member))
        else:
            server = i['Channels']['Joins']['Channel']
            await bot.send_message(server, fmt.format(member))


@bot.event
async def on_member_ban(member):
    server = member.server
    fmt = '**{0.mention}** was banned!'
    i = giveAllowances(server)
    if i['Channels']['Bans']['Enabled'] == 'True':
        if i['Channels']['Bans']['Channel'] == '':
            await bot.send_message(server, fmt.format(member))
        else:
            server = i['Channels']['Bans']['Channel']
            await bot.send_message(server, fmt.format(member))


@bot.event
async def on_member_remove(member):
    server = member.server
    fmt = '**{0.mention}** lol rip'
    i = giveAllowances(server)
    if i['Channels']['Leaves']['Enabled'] == 'True':
        if i['Channels']['Leaves']['Channel'] == '':
            await bot.send_message(server, fmt.format(member))
        else:
            server = i['Channels']['Leaves']['Channel']
            await bot.send_message(server, fmt.format(member))


@bot.event
async def on_ready():
    print("----------")
    print("Logged in as:")
    print("    "+str(bot.user.name))
    print("    "+str(bot.user.id))
    gameThingy = ".help [ApplePy v0.3]"
    await bot.change_status(discord.Game(name=gameThingy))
    print("Game changed to '%s'." % gameThingy)
    print("----------")

    try:
        with open(workingDirectory+'restartFile.txt','r') as a:
            cha = discord.Object(id=a.readlines()[0])
        await bot.send_message(cha, "Restarted.")
        os.remove(workingDirectory+'restartFile.txt')
    except FileNotFoundError:
        pass

    startup_extensions = ['fun', 'search', 'permissions', 'counting','customcommands','strawpolling']
    for extension in startup_extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            print('Failed to load extension {}\n{}'.format(extension, exc))


@bot.event
async def on_message(message):

    continueWithComms = True
    aq = giveAllowances(message.server.id)

    if message.author.id != bot.user.id:

        try:
            with open(serverConfigs+message.server.id+'.json','r',encoding='utf-8') as data_file:    
                customCommands = json.load(data_file)['CustomCommands']

            try:
                await bot.send_message(message.channel, eval(customCommands[message.content.lower()]).translate(non_bmp_map) )
            except KeyError:
                pass
        except KeyError:
            pass
        except FileNotFoundError:
            pass

        if 'imgur.com/' in message.content and aq['ImgurAlbum']['Enabled'] == 'True':
            if 'imgur.com/a/' in message.content:
                imLink = message.content.split('imgur.com/a/')[1][:5]
            elif 'imgur.com/gallery/' in message.content:
                imLink = message.content.split('imgur.com/gallery/')[1][:5]
            try:
                imLink = imgurAlbumToItems(imLink)
                await bot.send_message(message.channel, '%s\n%s' %(message.author.mention, imLink))
            except UnboundLocalError:
                pass

    if continueWithComms:
        await bot.process_commands(message)

bot.run(discordToken)
