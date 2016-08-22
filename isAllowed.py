import os
import json
import discord

workingDirectory = os.path.dirname(os.path.realpath(__file__)) + \
                   "\\botTxtFiles\\"
serverConfigs = os.path.dirname(os.path.realpath(__file__)) + \
                "\\botTxtFiles\\serverConfigs\\"
with open('%sdiscordTokens.json' %workingDirectory) as data_file:    
    tokens = json.load(data_file)


helpText = {}


defSerCon = \
{
    "Commands":{},
    "Channels":{
        "Bans":{
            "Enabled":"False",
            "Channel":""
        }, 
        "RSS":{}, 
        "Joins":{
            "Enabled":"False",
            "Channel":""
        }, 
        "Leaves":{
            "Enabled":"False",
            "Channel":""
        }
    }, 
    "CustomCommands":{},
    "ImgurAlbum" : {
        "Enabled" : "False"
    }
}


def isAllowed(ctx, calledFunction):
    serverConStuff = None 
    try:
        with open(serverConfigs+ctx.message.server.id+'.json') as a:
            serverConStuff = json.load(a)
    except FileNotFoundError:
        with open(serverConfigs+ctx.message.server.id+'.json', 'w') as a:
            serverConStuff = defSerCon
            a.write(json.dumps(serverConStuff,indent=4))
        return True

    try:
        q = serverConStuff["Commands"][calledFunction]
    except KeyError:
        with open(serverConfigs+ctx.message.server.id+'.json', 'w') as a:
            serverConStuff["Commands"][calledFunction] = []
            a.write(json.dumps(serverConStuff,indent=4))
        return True

    if q == []:
        return True

    chekRol = [i.id for i in ctx.message.author.roles]
    
    for i in q:
        if i in chekRol:
            return True
    return False


def giveAllowances(ctx):
    if type(ctx) == str:
        serId = ctx
    else:
        try:
            serId = ctx.message.server.id
        except AttributeError:
            serId = ctx.id
    serverConStuff = None 
    try:
        with open(serverConfigs+serId+'.json') as a:
            serverConStuff = json.load(a)
    except FileNotFoundError:
        with open(serverConfigs+serId+'.json', 'w') as a:
            serverConStuff = defSerCon
            a.write(json.dumps(serverConStuff,indent=4))
    return serverConStuff

def writeAllow(ctx, jsonToWrite):
    if type(ctx) == str:
        serId = ctx
    else:
        try:
            serId = ctx.message.server.id
        except AttributeError:
            serId = ctx.id
            
    with open(serverConfigs+serId+'.json','w') as a:
        a.write(json.dumps(jsonToWrite,indent=4))

def givePerms(ctx):
    return ctx.message.channel.permissions_for(ctx.message.author)