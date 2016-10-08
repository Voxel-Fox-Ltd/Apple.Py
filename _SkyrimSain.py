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


@bot.event
async def on_member_join(member):
    server = member.server
    i = giveAllowances(server)
    if i['Joins']['Channel'] != '':
        server = discord.Object(i['Joins']['Channel'])
    if i['Joins']['Enabled'] == 'True':
        fmt = i['Joins']['Text'].replace('{mention}',member.mention).replace('{name}',member.name)
        await bot.send_message(server, fmt)


@bot.event
async def on_member_ban(member):
    server = member.server
    i = giveAllowances(server)
    if i['Bans']['Channel'] != '':
        server = discord.Object(i['Bans']['Channel'])
    if i['Bans']['Enabled'] == 'True':
        fmt = i['Bans']['Text'].replace('{mention}',member.mention).replace('{name}',member.name)
        await bot.send_message(server, fmt)


@bot.event
async def on_member_remove(member):
    server = member.server
    i = giveAllowances(server)
    if i['Leaves']['Channel'] != '':
        server = discord.Object(i['Leaves']['Channel'])
    if i['Leaves']['Enabled'] == 'True':
        fmt = i['Leaves']['Text'].replace('{mention}',member.mention).replace('{name}',member.name)
        await bot.send_message(server, fmt)


@bot.event
async def on_ready():
    print("----------")
    print("Logged in as:")
    print("    " + str(bot.user.name))
    print("    " + str(bot.user.id))
    gameThingy = ".help [ApplePy v0.5]"
    await bot.change_presence(game=discord.Game(name=gameThingy))
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
