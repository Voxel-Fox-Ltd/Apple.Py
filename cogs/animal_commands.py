from discord.ext import commands, vbu


class AnimalCommands(vbu.Cog):

    @commands.command(aliases=['kitty'])
    @commands.cooldown(1, 5, commands.BucketType.channel)
    @vbu.checks.is_config_set('api_keys', 'cat_api')
    async def cat(self, ctx: vbu.Context, *, breed: str = None):
        """
        Gives you some kitty pictures.
        """

        await ctx.trigger_typing()
        headers = {
            "User-Agent": self.bot.user_agent,
            "x-api-key": self.bot.config['api_keys']['cat_api']
        }
        params = {
            "limit": 1
        }
        if breed:
            params.update({"breed_ids": breed})
        async with self.bot.session.get("https://api.thecatapi.com/v1/images/search", params=params, headers=headers) as r:
            data = await r.json()
        if not data:
            return await ctx.send("Couldn't find that breed mate.")
        with vbu.Embed(use_random_colour=True) as embed:
            embed.set_image(url=data[0]['url'])
        await ctx.send(embed=embed)

    @commands.command(aliases=['doggo', 'puppy', 'pupper'])
    @commands.cooldown(1, 2, commands.BucketType.channel)
    async def dog(self, ctx: vbu.Context, *, breed: str = None):
        """
        Gives you some dog pictures.
        """

        await ctx.trigger_typing()
        headers = {"User-Agent": self.bot.user_agent}
        if breed is None:
            url = "https://dog.ceo/api/breeds/image/random"
        else:
            url = f"https://dog.ceo/api/breed/{breed.replace(' ', '/')}/images/random"
        async with self.bot.session.get(url, headers=headers) as r:
            data = await r.json()
        if data['status'] == "error":
            return await ctx.send("No dogs were found :(")
        with vbu.Embed(use_random_colour=True) as embed:
            embed.set_image(url=data['message'])
        await ctx.send(embed=embed)

    @commands.command(aliases=['foxo', 'foxxo'])
    @commands.cooldown(1, 5, commands.BucketType.channel)
    async def fox(self, ctx: vbu.Context):
        """
        Gives you some fox pictures.
        """

        await ctx.trigger_typing()
        headers = {"User-Agent": self.bot.user_agent}
        async with self.bot.session.get("https://randomfox.ca/floof/", headers=headers) as r:
            data = await r.json()
        with vbu.Embed(use_random_colour=True) as embed:
            embed.set_image(url=data['image'])
        await ctx.send(embed=embed)

    @commands.command(aliases=['birb'])
    @commands.cooldown(1, 5, commands.BucketType.channel)
    async def bird(self, ctx: vbu.Context):
        """
        Gives you some bird pictures.
        """

        await ctx.trigger_typing()
        headers = {"User-Agent": self.bot.user_agent}
        async with self.bot.session.get("https://some-random-api.ml/img/birb", headers=headers) as r:
            data = await r.json()
        with vbu.Embed(use_random_colour=True) as embed:
            embed.set_image(url=data['link'])
        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.channel)
    async def panda(self, ctx: vbu.Context):
        """
        Gives you some panda pictures.
        """

        await ctx.trigger_typing()
        headers = {"User-Agent": self.bot.user_agent}
        async with self.bot.session.get("https://some-random-api.ml/img/panda", headers=headers) as r:
            data = await r.json()
        with vbu.Embed(use_random_colour=True) as embed:
            embed.set_image(url=data['link'])
        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.channel)
    async def redpanda(self, ctx: vbu.Context):
        """
        Gives you some red panda pictures.
        """

        await ctx.trigger_typing()
        headers = {"User-Agent": self.bot.user_agent}
        async with self.bot.session.get("https://some-random-api.ml/img/red_panda", headers=headers) as r:
            data = await r.json()
        with vbu.Embed(use_random_colour=True) as embed:
            embed.set_image(url=data['link'])
        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.channel)
    async def koala(self, ctx: vbu.Context):
        """
        Gives you some koala pictures.
        """

        await ctx.trigger_typing()
        headers = {"User-Agent": self.bot.user_agent}
        async with self.bot.session.get("https://some-random-api.ml/img/koala", headers=headers) as r:
            data = await r.json()
        with vbu.Embed(use_random_colour=True) as embed:
            embed.set_image(url=data['link'])
        await ctx.send(embed=embed)


def setup(bot: vbu.Bot):
    x = AnimalCommands(bot)
    bot.add_cog(x)
