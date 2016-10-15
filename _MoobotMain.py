from isAllowed import *

# Create the bot
description = '''This is my bot I like to make it do things.'''
bot = commands.Bot(command_prefix=[','], description=description, pm_help=True)


# Create all of the tokens and keys
discordToken = tokens['Moobot']


@bot.event
async def on_ready():
    print("----------")
    print("Logged in as:")
    print("    " + str(bot.user.name))
    print("    " + str(bot.user.id))
    with open(workingDirectory+'game_moosic.txt') as a:
        gameThingy = a.read()
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
        if i.startswith('moobot_addon_'):
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

    await bot.process_commands(message)


bot.run(discordToken)
