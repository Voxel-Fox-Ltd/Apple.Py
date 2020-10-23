import json

from discord.ext import commands
import voxelbotutils as utils


class WolframAlpha(utils.Cog):

    @utils.command()
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    @utils.checks.is_config_set('api_keys', 'wolfram')
    async def wolfram(self, ctx, *, search:str):
        """
        Ping some data to WolframAlpha.
        """

        params = {
            "input": search,
            "appid": self.bot.config['api_keys']['wolfram'],
            "format": "image",
            "output": "json",
        }
        async with self.bot.session.get("https://api.wolframalpha.com/v2/query", params=params) as r:
            data = json.loads(await r.text())
        try:
            pod = data['queryresult']['pods'][1]
            await ctx.send(pod['subpods'][0]['img'])
            return await ctx.send(embed=utils.Embed(title=pod['title'], use_random_colour=True).set_image(pod['subpods'][0]['img']['src']))
        except (KeyError, IndexError):
            return await ctx.send("No results for that query!")


def setup(bot:utils.Bot):
    x = WolframAlpha(bot)
    bot.add_cog(x)
