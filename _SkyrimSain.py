import discord
import asyncio
import requests
import os
import random
import json
import datetime
import praw
import sys
import xmltodict
from discord.ext import commands
import logging
from isAllowed import *
from imgurpython import ImgurClient



startTime = datetime.datetime.now()


logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='%sbot.log' %workingDirectory, encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


description = '''This is my bot I like to make it do things.'''
bot = commands.Bot(command_prefix='.', description=description, pm_help=True)


def randFromList(listThing):
    return listThing[random.randint(0, len(listThing)-1)]


def txtFileToList(nameOfFile):
    nameOfFile = workingDirectory + nameOfFile + '.txt'
    file = open(nameOfFile, 'r', encoding="utf-8")
    fileContent = file.read()
    file.close()
    fileContent = fileContent.split("\n")
    return fileContent


discordToken = tokens['Skybot']

mashapeKey = {"X-Mashape-Key":
              tokens['Mashape']}
htmlHead = {'Accept-Endoding': 'identity'}
BOT_CLIENT_ID = tokens['SkybotID']
imgurUsr = ImgurClient(tokens['ImgurClient'], tokens['ImgurSecret'])
non_bmp_map = dict.fromkeys(range(0x10000, sys.maxunicode + 1), 0xfffd)


notallowed = "You are not allowed to use that command."
waitmessage = "Please wait..."


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


async def printToDiscord(channel, text):
    return await bot.send_message(channel, text)


@bot.command(pass_context=True,description='Echos what the user says.')
async def echo(ctx):
    if isAllowed(ctx, sys._getframe().f_code.co_name):
        print("Echoing :: %s" % ctx.message.content.split(' ',1)[1])
        a = ctx.message.content.split(' ',1)[1]
        await bot.say(a)
        return 
    else:
        await bot.say(notallowed)


@bot.command(pass_context=True,description='Echos what the user says.')
async def echochannel(ctx):
    if isAllowed(ctx, sys._getframe().f_code.co_name):
        a = ctx.message.content.split(' ',2)[2]
        chan = discord.Object(ctx.message.raw_channel_mentions[0])
        await bot.send_message(chan, a)
        return 
    else:
        await bot.say(notallowed)


@bot.command(pass_context=True,description='Gives you an invte link for the bot.')
async def invite(ctx):
    if isAllowed(ctx, sys._getframe().f_code.co_name):
        print("Told someone the invite link.")
        q = "https://discordapp.com/oauth2/authorize?scope=bot&client_id=%s&permissions=0x1c016c10" \
               % BOT_CLIENT_ID
        await bot.say(q)
    else:
        await bot.say(notallowed)
    return


@bot.command(pass_context=True,description='Removes x amount of messages from chat.')
async def purge(ctx):
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


@bot.command(pass_context=True,description='Changes the nickname of the bot.')
async def rename(ctx):
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


@bot.command(pass_context=True,description='Checks the uptime of the server.')
async def uptime(ctx):
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


@bot.command(pass_context=True,description='Changes the colour of the submitter to a hex code.')
async def ccolour(ctx):
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
                    except discord.errors.HTTPException:
                        pass
            print("Adding role to user.")
            await bot.add_roles(ctx.message.author, rrr)
            await bot.say("Changed user role colour.")
        except discord.errors.Forbidden:
            await bot.say("This bot does not have permissions to manage roles.")
        return
    else:
        await bot.say(notallowed)


@bot.command(pass_context=True,description='Restarts the bot.')
async def ex(ctx):
    if isAllowed(ctx, sys._getframe().f_code.co_name):
        toEx = ctx.message.content.split(' ',1)[1]
        await bot.say(execute(ctx, toEx))
    else:
        await bot.say(notallowed)
    return


def execute(ctx, toEx):
    ret = None 
    print(toEx)
    print(ret)
    exec(toEx)
    print(ret)
    return ret


@bot.command(pass_context=True,description='Restarts the bot.')
async def restart(ctx):
    if ctx.message.author.id == '141231597155385344':

        with open(workingDirectory+'restartFile.txt','w') as a:
            a.write(str(ctx.message.channel.id))
        await bot.say("Restarting...")

        os.execl(sys.executable, *([sys.executable]+sys.argv))
    else:
        await bot.say('You have to be the bot\'s creator to use this command.')
    return


@bot.command(pass_context=True,description='Kills the bot.')
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
async def on_member_remove(member):
    server = member.server
    fmt = '**{0.name}** lol rip'
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

    startup_extensions = ['fun', 'search', 'permissions', 'counting','customcommands']
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
                # toOutput = None
                # exec(customCommands[message.content.lower()])
                # await bot.send_message(message.channel, toOutput)
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
            imLink = imgurAlbumToItems(imLink)
            await bot.send_message(message.channel, '%s\n%s' %(message.author.mention, imLink))

    if continueWithComms:
        await bot.process_commands(message)

bot.run(discordToken)
