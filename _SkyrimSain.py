import discord
import asyncio
from discord.ext import commands
import os
import json
import datetime
import sys
import logging
from isAllowed import *
from imgurpython import ImgurClient
import requests


# Set up the start time for the restart command
startTime = datetime.datetime.now()


# Start up some logging for debugging
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='%sbot.log' %
                              workingDirectory, encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter(
    '%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


# Create the bot
description = '''This is my bot I like to make it do things.'''
bot = commands.Bot(command_prefix=['.','<@199136310416375808> '], description=description, pm_help=True)


# Create all of the tokens and keys
discordToken = tokens['Skybot']
mashapeKey = {"X-Mashape-Key":
              tokens['Mashape']}
htmlHead = {'Accept-Endoding': 'identity'}
BOT_CLIENT_ID = tokens['SkybotID']
imgurUsr = ImgurClient(tokens['ImgurClient'], tokens['ImgurSecret'])


# Make the bot more unicode-friendly
non_bmp_map = dict.fromkeys(range(0x10000, sys.maxunicode + 1), 0xfffd)


# This uses the imgur API to convert an album into a list of links
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


@bot.command(pass_context=True, help=helpText['echo'][1], brief=helpText['echo'][0])
async def echo(ctx):
    """Simply says back what the person says."""
    print("Echoing :: %s" % ctx.message.content.split(' ', 1)[1])
    try:
        chan = discord.Object(ctx.message.raw_channel_mentions[0])
        a = ctx.message.content.split(' ', 2)[2]
    except:
        chan = ctx.message.channel
        a = ctx.message.content.split(' ', 1)[1]
    await bot.send_message(chan, a)


@bot.command(pass_context=True, help=helpText['invite'][1], brief=helpText['invite'][0])
async def invite(ctx):
    """Gives the invite link for the bot."""
    print("Told someone the invite link.")
    q = "https://discordapp.com/oauth2/authorize?scope=bot&client_id=%s&permissions=0x1c016c10" \
        % BOT_CLIENT_ID
    await bot.say(q)


@bot.command()
async def git():
    """Plonks the link to my Github in chat."""
    await bot.say("Feel free to fork me!\n<https://github.com/4Kaylum/SkyBot>")


@bot.command(pass_context=True, help=helpText['purge'][1], brief=helpText['purge'][0])
async def purge(ctx):
    """Purges x messages from the channel."""
    if allowUse(ctx, ['manage_messages']):
        try:
            a = int(ctx.message.content.split(" ")[1])
            if a > 200:
                await bot.say("No, fuck you.")
                return
        except ValueError:
            await bot.say("Please provide a value.")
            return
        print("Deleting %s messages." % a)
        await bot.purge_from(ctx.message.channel, limit=a)
    else:
        await bot.say(notallowed)


@bot.command(pass_context=True, help=helpText['rename'][1], brief=helpText['rename'][0])
async def rename(ctx):
    """Renames the bot."""
    if allowUse(ctx, ['manage_nicknames']):
        try:
            ser = ctx.message.mentions[0]
            z = ctx.message.content.split(' ')
            del z[0]
            del z[-1]
            toRn = ' '.join(z)
        except IndexError:
            ser = ctx.message.server.get_member_named(bot.user.name)
            toRn = ctx.message.content.split(' ', 1)[1]
        try:
            try:
                await bot.change_nickname(ser, toRn)
                x = "Changed nickname to '%s'." % toRn
            except IndexError:
                await bot.change_nickname(ser, '')
                x = "Removed nickname."
            await bot.say(x)
        except discord.errors.Forbidden:
            await bot.say("The bot is not allowed to change nickname [of that user].")
    else:
        await bot.say(notallowed)


def is_bot(m):
    if m.author == bot.user:
        if m.content.startswith('Cleaned up'):
            return False
        else:
            return True


@bot.command(pass_context=True, help=helpText['clean'][1], brief=helpText['clean'][0])
async def clean(ctx):
    """Deletes the bot's messages from the last 50 posted to the channel."""
    q = await bot.purge_from(ctx.message.channel, limit=50, check=is_bot)
    await bot.say("Cleaned up **{}** messages".format(len(q)))


@bot.command(pass_context=True, help=helpText['uptime'][1], brief=helpText['uptime'][0])
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
%s seconds```''' % (hours, minutes, up)

    userCount = []
    for i in bot.servers:
        for o in i.members:
            if o not in userCount:
                userCount.append(o)

    outplut = '''```On %s servers
Serving %s unique users```''' % (len(bot.servers), len(userCount))

    superOut = outplut + '\n' + out
    await bot.say(superOut)


@bot.command(pass_context=True, aliases=['ccolor'], help=helpText['ccolour'][1], brief=helpText['ccolour'][0])
async def ccolour(ctx):
    """Changes the users colour to the mentioned hex code."""
    if allowUse(ctx, ['manage_roles']):
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
            usrQ = ctx.message.mentions[0]
        except IndexError:
            usrQ = ctx.message.author

        try:
            for role in ctx.message.server.roles:
                if str(role.name) == str(usrQ):
                    await bot.edit_role(ctx.message.server, role, colour=discord.Colour(int(hexc, 16)))
                    rrr = role
                    print("Editing role :: %s" % str(role.name))
                    flag = True
            if flag == False:
                print("Creating role :: %s" % str(usrQ))
                rrr = await bot.create_role(ctx.message.server, name=str(usrQ), colour=discord.Colour(int(hexc, 16)), permissions=discord.Permissions(permissions=0))
                for i in range(0, 500, 1):
                    try:
                        await bot.move_role(ctx.message.server, rrr, i)
                        break
                    except discord.errors.InvalidArgument:
                        pass
                    except discord.ext.commands.errors.CommandInvokeError:
                        pass
            print("Adding role to user.")
            await bot.add_roles(usrQ, rrr)
            await bot.say("Changed user role colour.")
        except discord.errors.Forbidden:
            await bot.say("This bot does not have permissions to manage roles [for that user].")
    else:
        await bot.say(notallowed)


@bot.command(pass_context=True)
async def ping(ctx):
    channelName = ctx.message.content.split(' ',1)[1]
    channel = discord.utils.get(ctx.message.server.channels, name=channelName, type=discord.ChannelType.voice)
    if channel == None:
        await bot.say("I could not find a VC under that name.")
        return
    x = []
    for i in channel.voice_members:
        x.append(i.mention)
    await bot.say(' '.join(x))


@bot.event
async def on_member_join(member):
    server = member.server
    fmt = '**{0.mention}** hi welcome i love you.'
    i = giveAllowances(server)
    if i['Joins']['Channel'] != '':
        server = discord.Object(i['Joins']['Channel'])
    if i['Joins']['Enabled'] == 'True':
        try:
            await bot.send_message(server, fmt.format(member))
        except:
            await bot.send_message(member.server, fmt.format(member))


@bot.event
async def on_member_ban(member):
    server = member.server
    fmt = '**{0.mention}** was banned!'
    i = giveAllowances(server)
    if i['Bans']['Channel'] != '':
        server = discord.Object(i['Bans']['Channel'])
    if i['Bans']['Enabled'] == 'True':
        try:
            await bot.send_message(server, fmt.format(member))
        except:
            await bot.send_message(member.server, fmt.format(member))


@bot.event
async def on_member_remove(member):
    server = member.server
    fmt = '**{0.mention}** lol rip'
    i = giveAllowances(server)
    if i['Leaves']['Channel'] != '':
        server = discord.Object(i['Leaves']['Channel'])
    if i['Leaves']['Enabled'] == 'True':
        try:
            await bot.send_message(server, fmt.format(member))
        except:
            await bot.send_message(member.server, fmt.format(member))


@bot.event
async def on_ready():
    print("----------")
    print("Logged in as:")
    print("    " + str(bot.user.name))
    print("    " + str(bot.user.id))
    gameThingy = ".help [ApplePy v0.5]"
    await bot.change_status(discord.Game(name=gameThingy))
    print("Game changed to '%s'." % gameThingy)
    print("----------")

    try:
        with open(workingDirectory + 'restartFile.txt', 'r') as a:
            cha = discord.Object(id=a.readlines()[0])
        await bot.send_message(cha, "Restarted.")
        os.remove(workingDirectory + 'restartFile.txt')
    except FileNotFoundError:
        pass

    startup_extensions = []
    for i in os.listdir(os.path.dirname(os.path.realpath(__file__))):
        if i.startswith('addon_'):
            startup_extensions.append(i[:-3])
    for extension in startup_extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            print('Failed to load extension {}\n{}'.format(extension, exc))


@bot.event
async def on_message(message):

    if message.author.bot:
        return

    continueWithComms = True
    aq = giveAllowances(message.server.id)

    if message.author.id != bot.user.id:

        try:
            with open(serverConfigs + message.server.id + '.json', 'r', encoding='utf-8') as data_file:
                customCommands = json.load(data_file)['CustomCommands']

            try:
                await bot.send_message(message.channel, eval(customCommands[message.content.lower()]).translate(non_bmp_map))
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
                await bot.send_message(message.channel, '%s\n%s' % (message.author.mention, imLink))
            except UnboundLocalError:
                pass

    if continueWithComms:
        await bot.process_commands(message)

bot.run(discordToken)
