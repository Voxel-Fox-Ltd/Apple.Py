import discord
from discord.ext import commands
from google import search
import esix
import wolframalpha
import praw
import json
import os
from imgurpython import ImgurClient
from steam.api import interface
import wikipedia
import steam
import datetime
import sys
import random
from microsofttranslator import *
from isAllowed import *


steam.api.key.set(tokens['Steam'])
wolfClient = wolframalpha.Client(tokens['Wolfram'])
furryPorn = 'https://e621.net/post/index.json?'
r_e = praw.Reddit(user_agent="A post searcher for a Discord user.")
imgurUsr = ImgurClient(tokens['ImgurClient'], tokens['ImgurSecret'])
translator = Translator(tokens['MSTransID'], tokens['MSTransSecret'])


notallowed = "You are not allowed to use that command."
waitmessage = "Please wait..."


def getSteamIDFromURL(urlInQuestion):
    print("    Converting vanity url...")
    van = steam.user.vanity_url(urlInQuestion)
    van = van.id64
    return van


def steamGameGetter(userIdentity):
    print("    Getting user's games...")
    games = interface('IPlayerService').GetOwnedGames(
        steamid=userIdentity, include_appinfo=1, aggressive=True)
    x = []
    for i in games['response']['games']:
        x.append(i['name'])
    return x


def steamUserComparison(listOfUserGames):
    a = len(listOfUserGames) - 2
    b = 1
    t = list(set(listOfUserGames[0]).intersection(listOfUserGames[b]))
    while a > 0:
        b += 1
        t = list(set(t).intersection(listOfUserGames[b]))
        a -= 1
    return t


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


class Search():

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True, description='Compares the games that you and any number of given Steam users have.')
    async def sc(self, ctx):
        edit = await self.bot.say(waitmessage)
        print("Comparing Steam users.")
        users = ctx.message.content.split(' ', 1)[1].split(" ")
        users2 = []
        for i in users:
            aye = i.split("/")
            if aye[-1] == "":
                aye = aye[-2]
            else:
                aye = aye[-1]
            try:
                int(aye)
            except ValueError:
                aye = getSteamIDFromURL(i)
            users2.append(aye)
        for i in users2:
            print("    ID :: %s" % i)
        x = []
        for i in users2:
            x.append(steamGameGetter(i))
        z = steamUserComparison(x)
        z.sort()
        v = "You have these games in common :: \n```"
        for i in z:
            v += "* %s\n" % i
        v = v[:-1] + '```'
        print("    Done.")
        if len(v) > 2000:
            await self.bot.edit_message(edit, "This message would be over 2000 characters.")
            return
        await self.bot.edit_message(edit, v)

    @commands.command(pass_context=True)
    async def trans(self, ctx):
        toChange = ctx.message.content.split(' ', 2)[2]
        langTo = ctx.message.content.split(' ', 2)[1]
        if langTo not in translator.get_languages():
            await self.bot.say("The language provided is not supported.")
            return

        translatedText = translator.translate(toChange, langTo)
        await self.bot.say(translatedText)

    @commands.command(pass_context=True, description='Returns the result of a Google search.', enabled=True)
    async def sg(self, ctx):
        edit = await self.bot.say(waitmessage)
        query = ctx.message.content.split(' ', 1)[1]
        print("Searching Google :: %s" % query)
        for i in search(query):
            await self.bot.edit_message(edit, i)
            return

    @commands.command(pass_context=True, description='Gives info on the mentioned user.')
    async def info(self, ctx):
        mea = ctx.message
        try:
            x = mea.mentions[0]
            avatar = str(x.avatar_url)
            username = str(x.name)
            display = str(x.display_name)
            idthing = str(x.id)
            botacc = str(x.bot)
            created = str(x.joined_at)[:-10]
            age = str(datetime.datetime.now() - x.joined_at).split(",")[0]
            roles = ""
            for i in x.roles:
                roles += str(i) + ', '  # str(x.roles)
            z = """%s
```
Username :: %s
 Display :: %s
      ID :: %s
     Bot :: %s
  Joined :: %s (Age %s)
   Roles :: %s
```""" % (avatar, username, display, idthing, botacc, created, age, roles[11:-2])

        except IndexError:
            z = "You need to mention a user in your message."

        print("Giving info on user :: %s" % mea.content.split(' ', 1)[1])
        await self.bot.say(z)
        return

    @commands.command(pass_context=True, description='Searches Wolfram Alpha.')
    async def w(self, ctx):
        edit = await self.bot.say(waitmessage)
        message = ctx.message
        print("Getting query to Wolfram :: %s" %
              message.content.split(' ', 1)[1])
        res = wolfClient.query(message.content.split(' ', 1)[1])
        print("    Sent and recieved.")
        # try:
        a = "```\n"
        for pod in res.pods:
            try:
                a += pod.text + "\n"
            except TypeError:
                pass
        a = a + "```"
        if a == "```\n```":
            a = "```Could not find any results for this query.```"
        print("    Result ::")
        x = a[3:-3]
        print('        ', end="")
        for i in x:
            if i == "\n":
                i = '\n        '
            print(i, end="")

        q = 0
        z = ''
        for pod in res.pods:
            # await self.bot.say(pod.main)
            z = z + pod.img + '\n'
            q += 1
            # if q == 4: break

        await self.bot.edit_message(edit, z)
        return

    @commands.command(pass_context=True, description='Searches Wikipedia for a given string.')
    async def wp(self, ctx):
        edit = await self.bot.say(waitmessage)
        searchTerm = ctx.message.content.split(' ', 1)[1]
        try:
            page = wikipedia.page(searchTerm)
            await bot.edit_message(edit, "**%s**\n```%s```\n'%s'" % (page.title, wikipedia.summary(searchTerm, sentences=10), page.url))
        except wikipedia.exceptions.DisambiguationError:
            page = wikipedia.search(searchTerm)
            toPost = ''
            for i in page:
                toPost = toPost + '* %s\n' % i
            toPost = '```%s```' % toPost[:-1]
            await self.bot.edit_message(edit, "Please specify ::\n%s" % toPost)
        except Exception as e:
            await self.bot.edit_message(exit, "Unknown error. Please alert {}.\n\n```\n{}```".format(discord.Object("141231597155385344").mention, str(repr(e))))
        return

    @commands.command(pass_context=True, description='Searches a subreddit for a query.')
    async def sr(self, ctx):
        edit = await self.bot.say(waitmessage)
        mes = ctx.message.content
        sub = mes.split(" ")[1]
        try:
            que = mes.split(' ', 2)[2]
        except IndexError:
            await self.bot.edit_message(edit, "Please provide a subreddit/query.")
            return

        try:
            search = r_e.search(que, subreddit=r_e.get_subreddit(sub))
            ret = []
            for i in search:
                ret.append(i)
                break
            ret = ret[0]
            rUrl = ret.url
            if 'imgur' in rUrl.lower():
                rUrl = imgurAlbumToItems(rUrl)
            await self.bot.edit_message(edit, '**%s**\n%s' % (ret.title, rUrl))

        except praw.errors.InvalidSubreddit:
            await bot.edit_message(edit, "That subreddit does not exist.")
        except IndexError:
            await self.bot.edit_message(edit, "There are no results for this search term.")
        return

    @commands.command(pass_context=True, description='Returns the result of a Imgur search.')
    async def si(self, ctx):
        edit = await self.bot.say(waitmessage)
        query = ctx.message.content.split(' ', 1)[1]
        if query == '':
            await self.bot.edit_message(edit, "Please provide a search term.")
            return

        print("Searching Imgur :: %s" % query)
        for i in imgurUsr.gallery_search(query, sort='viral'):
            await self.bot.edit_message(edit, '**%s**\n%s' % (i.title, imgurAlbumToItems(i)))
            return

    @commands.command(pass_context=True, description='Searches E621 for some furry shit.', enabled=False)
    async def furry(self, ctx):
        edit = await self.bot.say(waitmessage)
        try:
            query = ctx.message.content.split(' ', 1)[1]
        except IndexError:
            with open(workingDirectory + "furrySearches.txt") as a:
                query = random.choice(a.read().split('\n'))
        query += ' -type:swf -type:webm'
        print("Submitting query to E621 :: %s" % query)
        search = esix.post.search(query, limit=1)
        try:
            x = [f.file_url for f in search]
            print("    Found :: %s" % x[0])
            z = x[0]
        except:
            z = "Couldn't find anything for that query."

        await self.bot.edit_message(edit, z)
        return


def setup(bot):
    bot.add_cog(Search(bot))
