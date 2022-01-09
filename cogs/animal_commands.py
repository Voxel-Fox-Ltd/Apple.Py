from discord.ext import commands, vbu

from .types.bot import Bot


class AnimalCommands(vbu.Cog[Bot]):

    @commands.command(
        aliases=['kitty'],
        application_command_meta=commands.ApplicationCommandMeta(),
    )
    @commands.defer()
    @commands.cooldown(1, 5, commands.BucketType.channel)
    @vbu.checks.is_config_set('api_keys', 'cat_api')
    async def cat(self, ctx: commands.Context):
        """
        Give you a cat picture!
        """

        await ctx.trigger_typing()
        headers = {
            "User-Agent": self.bot.user_agent,
            "x-api-key": self.bot.config['api_keys']['cat_api']
        }
        params = {
            "limit": 1
        }
        async with self.bot.session.get("https://api.thecatapi.com/v1/images/search", params=params, headers=headers) as r:
            data = await r.json()
        if not data:
            return await ctx.send("I couldn't find that breed of cat.")
        with vbu.Embed(use_random_colour=True) as embed:
            embed.set_image(url=data[0]['url'])
        await ctx.send(embed=embed)

    @commands.command(aliases=['doggo', 'puppy', 'pupper'])
    @commands.defer()
    @commands.cooldown(1, 2, commands.BucketType.channel)
    async def dog(self, ctx: commands.Context):
        """
        Give you a doggo picture!
        """

        await ctx.trigger_typing()
        headers = {"User-Agent": self.bot.user_agent}
        url = "https://dog.ceo/api/breeds/image/random"
        async with self.bot.session.get(url, headers=headers) as r:
            data = await r.json()
        if data['status'] == "error":
            return await ctx.send("No dogs were found :(")
        with vbu.Embed(use_random_colour=True) as embed:
            embed.set_image(url=data['message'])
        await ctx.send(embed=embed)

    @commands.command(aliases=['foxo', 'foxxo'])
    @commands.cooldown(1, 5, commands.BucketType.channel)
    async def fox(self, ctx: commands.Context):
        """
        Give you a foxxo picture!
        """

        await ctx.trigger_typing()
        headers = {"User-Agent": self.bot.user_agent}
        async with self.bot.session.get("https://randomfox.ca/floof/", headers=headers) as r:
            data = await r.json()
        with vbu.Embed(use_random_colour=True) as embed:
            embed.set_image(url=data['image'])
        await ctx.send(embed=embed)

    # @commands.command(aliases=['birb'])
    # @commands.cooldown(1, 5, commands.BucketType.channel)
    # async def bird(self, ctx: commands.Context):
    #     """
    #     Gives you some bird pictures.
    #     """

    #     await ctx.trigger_typing()
    #     headers = {"User-Agent": self.bot.user_agent}
    #     async with self.bot.session.get("https://some-random-api.ml/img/birb", headers=headers) as r:
    #         data = await r.json()
    #     with vbu.Embed(use_random_colour=True) as embed:
    #         embed.set_image(url=data['link'])
    #     await ctx.send(embed=embed)

    # @commands.command()
    # @commands.cooldown(1, 5, commands.BucketType.channel)
    # async def panda(self, ctx: commands.Context):
    #     """
    #     Gives you some panda pictures.
    #     """

    #     await ctx.trigger_typing()
    #     headers = {"User-Agent": self.bot.user_agent}
    #     async with self.bot.session.get("https://some-random-api.ml/img/panda", headers=headers) as r:
    #         data = await r.json()
    #     with vbu.Embed(use_random_colour=True) as embed:
    #         embed.set_image(url=data['link'])
    #     await ctx.send(embed=embed)

    # @commands.command()
    # @commands.cooldown(1, 5, commands.BucketType.channel)
    # async def redpanda(self, ctx: commands.Context):
    #     """
    #     Gives you some red panda pictures.
    #     """

    #     await ctx.trigger_typing()
    #     headers = {"User-Agent": self.bot.user_agent}
    #     async with self.bot.session.get("https://some-random-api.ml/img/red_panda", headers=headers) as r:
    #         data = await r.json()
    #     with vbu.Embed(use_random_colour=True) as embed:
    #         embed.set_image(url=data['link'])
    #     await ctx.send(embed=embed)

    # @commands.command()
    # @commands.cooldown(1, 5, commands.BucketType.channel)
    # async def koala(self, ctx: commands.Context):
    #     """
    #     Gives you some koala pictures.
    #     """

    #     await ctx.trigger_typing()
    #     headers = {"User-Agent": self.bot.user_agent}
    #     async with self.bot.session.get("https://some-random-api.ml/img/koala", headers=headers) as r:
    #         data = await r.json()
    #     with vbu.Embed(use_random_colour=True) as embed:
    #         embed.set_image(url=data['link'])
    #     await ctx.send(embed=embed)


def setup(bot: Bot):
    x = AnimalCommands(bot)
    bot.add_cog(x)
