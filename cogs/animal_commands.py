from discord.ext import commands, vbu

from .types.bot import Bot


class AnimalCommands(vbu.Cog[Bot]):

    @commands.command(
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
        r = await self.bot.session.get(
            "https://api.thecatapi.com/v1/images/search",
            params=params,
            headers=headers,
        )
        data = await r.json()
        if not data:
            return await ctx.send("I couldn't find that breed of cat.")
        with vbu.Embed(use_random_colour=True) as embed:
            embed.set_image(url=data[0]['url'])
        await ctx.send(embed=embed)


def setup(bot: Bot):
    x = AnimalCommands(bot)
    bot.add_cog(x)
