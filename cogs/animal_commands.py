from discord.ext import commands

from cogs import utils


class AnimalCommands(utils.Cog):

    @commands.command(cls=utils.Command, aliases=['kitty'])
    @utils.cooldown.cooldown(1, 5, commands.BucketType.channel)
    async def cat(self, ctx:utils.Context):
        """Gives you some kitty pictures"""

        await ctx.channel.trigger_typing()
        headers = {"User-Agent": "Apple.py/0.0.1 - Discord@Caleb#2831"}
        async with self.bot.session.get("https://api.thecatapi.com/v1/images/search", headers=headers) as r:
            data = await r.json()
        with utils.Embed(use_random_colour=True) as embed:
            embed.set_image(url=data[0]['url'])
        await ctx.send(embed=embed)

    @commands.command(cls=utils.Command, aliases=['doggo', 'puppy', 'pupper'])
    @utils.cooldown.cooldown(1, 5, commands.BucketType.channel)
    async def dog(self, ctx:utils.Context):
        """Gives you some dog pictures"""

        await ctx.channel.trigger_typing()
        headers = {"User-Agent": "Apple.py/0.0.1 - Discord@Caleb#2831"}
        async with self.bot.session.get("https://dog.ceo/api/breeds/image/random", headers=headers) as r:
            data = await r.json()
        with utils.Embed(use_random_colour=True) as embed:
            embed.set_image(url=data['message'])
        await ctx.send(embed=embed)

    @commands.command(cls=utils.Command, aliases=['foxo', 'foxxo'])
    @utils.cooldown.cooldown(1, 5, commands.BucketType.channel)
    async def fox(self, ctx:utils.Context):
        """Gives you some fox pictures"""

        await ctx.channel.trigger_typing()
        headers = {"User-Agent": "Apple.py/0.0.1 - Discord@Caleb#2831"}
        async with self.bot.session.get("https://randomfox.ca/floof/", headers=headers) as r:
            data = await r.json()
        with utils.Embed(use_random_colour=True) as embed:
            embed.set_image(url=data['image'])
        await ctx.send(embed=embed)

    @commands.command(cls=utils.Command, aliases=['birb'])
    @utils.cooldown.cooldown(1, 5, commands.BucketType.channel)
    async def bird(self, ctx:utils.Context):
        """Gives you some bird pictures"""

        await ctx.channel.trigger_typing()
        headers = {"User-Agent": "Apple.py/0.0.1 - Discord@Caleb#2831"}
        async with self.bot.session.get("https://some-random-api.ml/img/birb", headers=headers) as r:
            data = await r.json()
        with utils.Embed(use_random_colour=True) as embed:
            embed.set_image(url=data['link'])
        await ctx.send(embed=embed)

    @commands.command(cls=utils.Command)
    @utils.cooldown.cooldown(1, 5, commands.BucketType.channel)
    async def panda(self, ctx:utils.Context):
        """Gives you some panda pictures"""

        await ctx.channel.trigger_typing()
        headers = {"User-Agent": "Apple.py/0.0.1 - Discord@Caleb#2831"}
        async with self.bot.session.get("https://some-random-api.ml/img/panda", headers=headers) as r:
            data = await r.json()
        with utils.Embed(use_random_colour=True) as embed:
            embed.set_image(url=data['link'])
        await ctx.send(embed=embed)

    @commands.command(cls=utils.Command)
    @utils.cooldown.cooldown(1, 5, commands.BucketType.channel)
    async def redpanda(self, ctx:utils.Context):
        """Gives you some red panda pictures"""

        await ctx.channel.trigger_typing()
        headers = {"User-Agent": "Apple.py/0.0.1 - Discord@Caleb#2831"}
        async with self.bot.session.get("https://some-random-api.ml/img/red_panda", headers=headers) as r:
            data = await r.json()
        with utils.Embed(use_random_colour=True) as embed:
            embed.set_image(url=data['link'])
        await ctx.send(embed=embed)

    @commands.command(cls=utils.Command)
    @utils.cooldown.cooldown(1, 5, commands.BucketType.channel)
    async def koala(self, ctx:utils.Context):
        """Gives you some koala pictures"""

        await ctx.channel.trigger_typing()
        headers = {"User-Agent": "Apple.py/0.0.1 - Discord@Caleb#2831"}
        async with self.bot.session.get("https://some-random-api.ml/img/koala", headers=headers) as r:
            data = await r.json()
        with utils.Embed(use_random_colour=True) as embed:
            embed.set_image(url=data['link'])
        await ctx.send(embed=embed)


def setup(bot:utils.Bot):
    x = AnimalCommands(bot)
    bot.add_cog(x)
