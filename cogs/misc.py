from discord.ext import commands

from cogs import utils


class Misc(utils.Cog):

    @commands.command(aliases=['git', 'code'], cls=utils.Command)
    @utils.checks.is_config_set('command_data', 'github')
    async def github(self, ctx:utils.Context):
        """Sends the GitHub Repository link"""

        await ctx.send(f"<{self.bot.config['command_data']['github']}>")

    @commands.command(aliases=['support', 'guild'], cls=utils.Command)
    @utils.checks.is_config_set('command_data', 'guild_invite')
    async def server(self, ctx:utils.Context):
        """Gives the invite to the support server"""

        await ctx.send(f"<{self.bot.config['command_data']['guild_invite']}>")

    @commands.command(aliases=['patreon'], cls=utils.Command)
    @utils.checks.is_config_set('command_data', 'patreon')
    async def donate(self, ctx:utils.Context):
        """Gives you the bot's creator's Patreon"""

        await ctx.send(f"<{self.bot.config['command_data']['patreon']}>")

    @commands.command(cls=utils.Command)
    async def invite(self, ctx:utils.Context):
        """Gives you the bot's invite link"""

        await ctx.send(f"<{self.bot.get_invite_link()}>")

    @commands.command(cls=utils.Command)
    async def echo(self, ctx:utils.Context, *, content:utils.converters.CleanContent):
        """Echos the given content into the channel"""

        await ctx.send(content)

    @commands.command(cls=utils.Command, hidden=True)
    @commands.is_owner()
    async def allbotinfo(self, ctx:utils.Context):
        """Gives info on all bots"""

        with utils.Embed(colour=0x1) as embed:
            embed.set_author_to_user(ctx.author)
            embed.description = """Woah guys it's time to shill my bots again how fun wew\nAlong with these I've also made a bunch of other bots - mostly as commissions (hmu xoxo) - but there are bots I make on streams sometimes, mostly pulling from <#602187744101269504>. Post there!"""
            embed.add_field("MarriageBot", """The reason you're all here, and the reason you all hate me. The classic family tree generation bot that only sometimes lets you stab others. This version of MarriageBot is _global_, so any family you make is available on every server that has MarriageBot in it. Run `m!help` for more, and `m!invite` for the invite link.""", False)
            embed.add_field("MarriageBot Gold", """The same as above but you get to forcemarry and forceadopt people, change how many children each role on your server can have, change the maximum amount of users in your family, etc, yup, fun fun fun. This version of MarriageBot has your family _exclusive_ to your server - any family you make will only exist there. Run `m!gold` for more.""", False)
            embed.add_field("Cerberus", """There's the classic problem with activity-for-role bots in that you eventually end up with people with the really active roles who haven't talked on your server in months. Cerberus is a response to that. With Cerberus you're able to track activity of users over time in order to give them activity roles based on the last 7 days of activity, rather than of all time.\nIf you _did_ want to set it up for all activity, however, you can easily import your role settings and message counts from Mee6 with just a simple command to ease the changeover. Run `'help` for more, and `'invite` for the invite link.""", False)
            embed.add_field("Synergy", """Synergy is basically a combination of all the interactions bots you've ever seen. Yknow those bots where you can run `hug @user` and whatever? This is that, but you're able to set up your own commands, your own responses, your own everything pretty much. Run `s;help` and see [the website](https://synergy.voxelfox.co.uk/) for more, and run `s;invite` for the invite link.""", False)
            embed.add_field("CookieBot", """Miss Cookie Clicker? Add CookieBot. Every server gets a unique kind of cookie, and you can run `c.mine` on your server to get yours. Trade with `c.give @user cookie type`, and run `c.inventory` to see all the cookies you have with you. Run `c.help` for more, and `c.invite` for the invite link.""", False)
            embed.add_field("Confessional", """Anonymous confessions, right here in your Discord server. Everyone who submits is anonymous, so nobody is ever found out. With that said, if you find that one confession is Not Your Style:tm:, you can still ban the user that sent it with a code on the confession. `x.createchannel <code>` to make a channel of your choice, and then you just DM it what you want to confess. Run `x.help` for more, and `x.invite` for the invite link.""", False)
            embed.add_field("Big Ben", """Everyone's favourite. It says "Bong" on the hour, every hour. #bong. Literally just one command and it's `bb.setbong` to set the channel it appears in. Run `bb.help` for more, and `bb.invite` for the invite link.""", False)
            embed.add_field("ProfileBot", """The hidden wonder. It allows you to create templates for your users to fill in, and then you can call them up at any time you want. I envisioned roleplay servers when I made it, but there are definitely uses outside of that. Run `,help` for more, and `,invite` for the invite link.""", False)
        await ctx.send(embed=embed)


def setup(bot:utils.Bot):
    x = Misc(bot)
    bot.add_cog(x)
