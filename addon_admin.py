from isAllowed import *


api = strawpoll.API()


class Admin():


    def __init__(self, bot):
        self.bot = bot


    @commands.command(pass_context=True)
    async def ban(self, ctx):
        """Ban command."""
        if allowUse(ctx, ['ban']) == False:
            await self.bot.say(notallowed)
            return
        await self.bot.say("**{}** has been banned.".format(ctx.message.mentions[0]))
        i = giveAllowances(ctx)
        if i['Bans']['Channel'] != '':
            server = discord.Object(i['Bans']['Channel'])
            await self.bot.send_message(server, "**{}** has been banned.".format(ctx.message.mentions[0]))
        await self.bot.ban(ctx.message.mentions[0])


    @commands.command(pass_context=True)
    async def kick(self, ctx):
        """Kick command."""
        if allowUse(ctx, ['kick']) == False:
            await self.bot.say(notallowed)
            return
        await self.bot.say("**{}** has been kicked.".format(ctx.message.mentions[0]))
        i = giveAllowances(ctx)
        if i['Bans']['Channel'] != '':
            server = discord.Object(i['Bans']['Channel'])
            await self.bot.send_message(server, "**{}** has been kicked.".format(ctx.message.mentions[0]))
        await self.bot.kick(ctx.message.mentions[0])


    @commands.group(pass_context=True,hidden=True)
    async def emoji(self, ctx):
        """Parent command for emoji usage"""
        pass


    @emoji.command(pass_context=True,name='add',hidden=True)
    async def emojiAdd(self, ctx):
        if allowUse(ctx, ['emoji']):
            emojiName = ctx.message.content.split(' ',3)[2]
            imgUrl = ctx.message.content.split(' ',3)[3]
            urlretrieve(imgUrl, 'emojiTEMP.png')
            a = open('emojiTEMP.png', 'rb')
            b = a.read()
            a.close()
            await self.bot.create_custom_emoji(server=ctx.message.server, name=emojiName, image=b)
            await self.bot.say("This emoji has been added.")
        else:
            await self.bot.say(notallowed)


    @commands.command(pass_context=True, help=helpText['pin'][1], brief=helpText['pin'][0])
    async def pin(self, ctx):
        """Pins the last message to the channel."""
        if allowUse(ctx, ['manage_messages']) == False:
            await self.bot.say(notallowed)
            return
        if len(ctx.message.content.split(' ')) == 1:
            async for i in self.bot.logs_from(ctx.message.channel, limit=2):
                message = i
        else:
            message = self.bot.get_message(
                ctx.message.channel, ctx.message.content.split(' ')[1])
            # message = discord.Object(ctx.message.content.split(' ')[1])
            await self.bot.say(ctx.message.content.split(' ')[1])
            await self.bot.say(type(message))
        try:
            await self.bot.pin_message(message)
        except discord.HTTPException as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            await self.bot.say("Something went wrong :: {}\nIt's likely that there are 50 pins in this channel already - that's the limit for Discord.".format(exc))
        except Exception as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            await self.bot.say("Something went wrong :: {}".format(exc))


    @commands.command(pass_context=True, help=helpText['rename'][1], brief=helpText['rename'][0])
    async def rename(self, ctx):
        """Renames the bot."""
        if allowUse(ctx, ['manage_nicknames','is_caleb']):
            try:
                ser = ctx.message.mentions[0]
                z = ctx.message.content.split(' ')
                del z[0]
                del z[-1]
                toRn = ' '.join(z)
            except IndexError:
                ser = ctx.message.server.get_member_named(self.bot.user.name)
                toRn = ctx.message.content.split(' ', 1)[1]
            try:
                try:
                    await self.bot.change_nickname(ser, toRn)
                    x = "Changed nickname to '%s'." % toRn
                except IndexError:
                    await self.bot.change_nickname(ser, '')
                    x = "Removed nickname."
                await self.bot.say(x)
            except discord.errors.Forbidden:
                await self.bot.say("The bot is not allowed to change nickname [of that user].")
        else:
            await self.bot.say(notallowed)


    @commands.command(pass_context=True, aliases=['ccolor'], help=helpText['ccolour'][1], brief=helpText['ccolour'][0])
    async def ccolour(self, ctx):
        """Changes the users colour to the mentioned hex code."""
        if allowUse(ctx, ['manage_roles']):
            flag = False
            try:
                hexc = ctx.message.content.split(' ')[1]
            except IndexError:
                await self.bot.say("Please provide a hex colour value.")
                return

            if hexc[0] == '#':
                hexc = hexc[1:]
            if len(hexc) != 6:
                await self.bot.say("Please provide a **hex** colour value.")
                return

            try:
                usrQ = ctx.message.mentions[0]
            except IndexError:
                usrQ = ctx.message.author

            try:
                for role in ctx.message.server.roles:
                    if str(role.name) == str(usrQ):
                        await self.bot.edit_role(ctx.message.server, role, colour=discord.Colour(int(hexc, 16)))
                        rrr = role
                        print("Editing role :: %s" % str(role.name))
                        flag = True
                if flag == False:
                    print("Creating role :: %s" % str(usrQ))
                    rrr = await self.bot.create_role(ctx.message.server, name=str(usrQ), colour=discord.Colour(int(hexc, 16)), permissions=discord.Permissions(permissions=0))
                    for i in range(0, 500, 1):
                        try:
                            await self.bot.move_role(ctx.message.server, rrr, i)
                            break
                        except discord.errors.InvalidArgument:
                            pass
                        except discord.ext.commands.errors.CommandInvokeError:
                            pass
                print("Adding role to user.")
                await self.bot.add_roles(usrQ, rrr)
                await self.bot.say("Changed user role colour.")
            except discord.errors.Forbidden:
                await self.bot.say("This bot does not have permissions to manage roles [for that user].")
        else:
            await self.bot.say(notallowed)


    @commands.command(pass_context=True, help=helpText['purge'][1], brief=helpText['purge'][0])
    async def purge(self, ctx):
        """Purges x messages from the channel."""
        if allowUse(ctx, ['manage_messages']):
            try:
                a = int(ctx.message.content.split(" ")[1])
                if a > 200:
                    await self.bot.say("No, fuck you.")
                    return
            except ValueError:
                await self.bot.say("Please provide a value.")
                return
            print("Deleting %s messages." % a)
            await self.bot.purge_from(ctx.message.channel, limit=a)
        else:
            await self.bot.say(notallowed)

    @commands.group(pass_context=True, help=helpText['channel'][1], brief=helpText['channel'][0])
    async def channel(self, ctx):
        """Parent command for channel."""
        if allowUse(ctx, ['manage_channels']) == False:
            await self.bot.say(notallowed)
            return
        elif ctx.invoked_subcommand is None:
            await self.bot.say("Please use `channel help` to see how to use this command properly.")

    @channel.command(name='create', aliases=['add', 'make'], pass_context=True)
    async def channelCreate(self, ctx):
        if allowUse(ctx, ['manage_channels']) == False:
            return
        serverObj = ctx.message.server
        channelName = ctx.message.content.split(' ', 2)[2]
        try:
            await self.bot.create_channel(serverObj, channelName)
            await self.bot.say("Channel created.")
        except Exception as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            await self.bot.say("Something went wrong :: {}".format(exc))

    @channel.command(name='delete', aliases=['del', 'remove', 'rem', 'rm'], pass_context=True)
    async def channelDelete(self, ctx):
        if allowUse(ctx, ['manage_channels']) == False:
            return
        try:
            toSet = ctx.message.raw_channel_mentions[0]
        except IndexError as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            await self.bot.say("Something went wrong :: {}".format(exc))
            return

        try:
            await self.bot.delete_channel(discord.Object(toSet))
            await self.bot.say("Channel deleted.")
        except Exception as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            await self.bot.say("Something went wrong :: {}".format(exc))
            return


def setup(bot):
    bot.add_cog(Admin(bot))
