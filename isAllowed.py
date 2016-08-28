import os
import json
import discord

workingDirectory = os.path.dirname(os.path.realpath(__file__)) + \
                   "\\botTxtFiles\\"
serverConfigs = os.path.dirname(os.path.realpath(__file__)) + \
                "\\botTxtFiles\\serverConfigs\\"
with open('%sdiscordTokens.json' %workingDirectory) as data_file:    
    tokens = json.load(data_file)


## Load up all the help text for every command.
with open('%shelpText.json' %workingDirectory) as data_file:    
    helpText = json.load(data_file)


defSerCon = \
{
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
    },
    "CustomCommands":{},
    "ImgurAlbum" : {
        "Enabled" : "False"
    }
}


## Checks some config files to see if certain commands are available for use.
## I've never actually used this properly so I'll phase it out for native permission
## checking inside of discord.
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


## Meant for use with the config commands, soon to be removed
## Writes the configuration changes to file.
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


## Returns the permissions of a given user.
def givePerms(ctx):
    return ctx.message.channel.permissions_for(ctx.message.author)


## Input a ctx and a list of permissions that the user will need..
## This will return true if a user has a certain permission, as asked for by
## the command call.
def allowUse(ctx,listOfNeeds,needsAll=True):
    allowLst = []
    permList = ctx.message.channel.permissions_for(ctx.message.author)
    convertDict = {
        'manage_messages':permList.manage_messages,
        'admin':permList.administrator,
        'kick_members':permList.kick_members,
        'kick':permList.kick_members,
        'ban_members':permList.ban_members,
        'ban':permList.ban_members,
        'manage_nicknames':permList.manage_nicknames
    }
    for i in listOfNeeds:
        allowLst.append(convertDict[i])

    if convertDict['admin']:
        return True 
    if needsAll:
        if False in allowLst:
            return False
        else:
            return True
    else:
        if True in allowLst:
            return True 
        else:
            return False