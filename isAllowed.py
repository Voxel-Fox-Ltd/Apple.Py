from skybotImports import *


notallowed = "You are not allowed to use that command."
waitmessage = "Please wait..."


workingDirectory = os.path.dirname(os.path.realpath(__file__)) + \
    "\\botTxtFiles\\"
serverConfigs = os.path.dirname(os.path.realpath(__file__)) + \
    "\\botTxtFiles\\serverConfigs\\"
with open('%sdiscordTokens.json' % workingDirectory) as data_file:
    tokens = json.load(data_file)


# Set up the start time for the restart command
startTime = datetime.datetime.now()


# Load up all the help text for every command.
with open('%shelpText.json' % workingDirectory) as data_file:
    helpText = json.load(data_file)


defSerCon = \
    {
        "Bans": {
            "Enabled": "False",
            "Channel": "",
            "Text" : "{mention} has been banned."
        },
        "RSS": {},
        "Joins": {
            "Enabled": "False",
            "Channel": "",
            "Text" : "{mention} hi welcome i love you"
        },
        "Leaves": {
            "Enabled": "False",
            "Channel": "",
            "Text" : "{mention} lol rip"
        },
        "CustomCommands": {},
        "ImgurAlbum": {
            "Enabled": "False"
        },
        "Streams" : {
            "Channel" : "",
            "TwitchTV" : {}
        }
    }


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
        with open(serverConfigs + serId + '.json') as a:
            serverConStuff = json.load(a)
    except FileNotFoundError:
        with open(serverConfigs + serId + '.json', 'w') as a:
            serverConStuff = defSerCon
            a.write(json.dumps(serverConStuff, indent=4))
    return serverConStuff


# Fixes a dictionary according to a reference. Pushes all keys into the input
def fixJson(inputDictionary, referenceDictionary=defSerCon):
    # inputDictionary = {"Joins": {"Enabled": "False","Channel": ""}}
    # referenceDictionary = {"Joins": {"Enabled": "False","Channel": "","Text" : "{mention} hi welcome i love you"}}
    for i in referenceDictionary:
        if type(referenceDictionary[i]) == dict:
            if i not in inputDictionary:
                inputDictionary[i] = referenceDictionary[i]
            else:
                inputDictionary[i] = fixJson(inputDictionary[i], referenceDictionary[i])
        else:
            if i in inputDictionary:
                pass
            else:
                inputDictionary[i] = referenceDictionary[i]
    return inputDictionary
    # writeAllow(ctx, inputDictionary)


# Meant for use with the config commands, soon to be removed
# Writes the configuration changes to file.
def writeAllow(ctx, jsonToWrite):
    if type(ctx) == str:
        serId = ctx
    else:
        try:
            serId = ctx.message.server.id
        except AttributeError:
            serId = ctx.id

    with open(serverConfigs + serId + '.json', 'w') as a:
        a.write(json.dumps(jsonToWrite, indent=4))


# Returns the permissions of a given user.
def givePerms(ctx):
    return ctx.message.channel.permissions_for(ctx.message.author)


# Input a ctx and a list of permissions that the user will need..
# This will return true if a user has a certain permission, as asked for by
# the command call.
def allowUse(ctx, listOfNeeds=['admin'], needsAll=False):
    allowLst = []
    permList = ctx.message.channel.permissions_for(ctx.message.author)
    convertDict = {
        'manage_messages': permList.manage_messages,
        'admin': permList.administrator,
        'kick_members': permList.kick_members,
        'kick': permList.kick_members,
        'ban_members': permList.ban_members,
        'ban': permList.ban_members,
        'manage_nicknames': permList.manage_nicknames,
        'manage_channels': permList.manage_channels,
        'manage_roles': permList.manage_roles,
        'manage_emoji':permList.manage_emojis,
        'emoji':permList.manage_emojis,
        'emojis':permList.manage_emojis,
        'manage_server':permList.manage_server,
        'is_caleb': ctx.message.author.id == '141231597155385344'
    }
    for i in listOfNeeds:
        allowLst.append(convertDict[i])

    if convertDict['admin'] and 'is_caleb' not in listOfNeeds:
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
