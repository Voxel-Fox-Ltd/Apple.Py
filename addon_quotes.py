from isAllowed import *


class Quote:

    def __init__(self, bot):
        self.bot = bot


    @commands.group(pass_context=True)
    async def quote(self, ctx):
        if ctx.invoked_subcommand == None:
            # See if they're trying to call a quote
            try:
                int(ctx.message.content.split(' ',1)[1])
            except:
                await self.bot.say("Use `.help quote` to see what I can do~")
                return

            # Call that quote
            try:
                i = giveAllowances(ctx)
                p = i['Quotes'][ctx.message.content.split(' ',1)[1]][0]
                await self.bot.say(p)
            except KeyError:
                await self.bot.say("That quote doesn't exist yet ;-;")


    @quote.command(pass_context=True,name='add')
    async def quoteAdd(self, ctx, *, message:str):
        i = giveAllowances(ctx)
        x = len(i['Quotes'])+1
        # Determine if the string is a message ID
        # Else string is string to be added
        i['Quotes'][str(x)] = [ctx.message.content.split(' ',2)[2],'```\nQuote added by {0.name} ({0.id}) at {1}GMT```'.format(ctx.message.author, str(datetime.datetime.now())[:-7])]
        writeAllow(ctx, i)
        await self.bot.say("Quote added as number `{}` c:".format(str(x)))


    @quote.command(pass_context=True,name='delete',aliases=['del','rem','remove'])
    async def quoteDel(self, ctx, *, num:str):
        i = giveAllowances(ctx)
        try:
            w = i['Quotes'][num]
        except KeyError:
            await self.bot.say("That quote doesn't exist anyway ;-;")
            return
        if i['Quotes'][num][0] == "This quote has been deleted ;-;":
            await self.bot.say("This quote has already been deleted.")
            return
        i['Quotes'][num] = ["This quote has been deleted ;-;",i['Quotes'][num][1]+'```\nQuote deleted by {0.name} ({0.id}) at {1}GMT```'.format(ctx.message.author, str(datetime.datetime.now())[:-7])]
        writeAllow(ctx, i)
        await self.bot.say("Quote `{}` deleted~".format(num))


    @quote.command(pass_context=True,name='info')
    async def quoteInfo(self, ctx):
        try:
            i = giveAllowances(ctx)
            p = i['Quotes'][ctx.message.content.split(' ',2)[2]][1]
            await self.bot.say(p)
        except KeyError:
            await self.bot.say("That quote doesn't exist yet ;-;")




def setup(bot):
    bot.add_cog(Quote(bot))
