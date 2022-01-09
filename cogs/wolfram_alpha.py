import json

import discord
from discord.ext import commands, vbu


class WolframAlpha(vbu.Cog):

    @commands.command(
        aliases=["wf", "wolframalpha", "wfa"],
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="search",
                    description="Your query for WolframAlpha.",
                    type=discord.ApplicationCommandOptionType.string,
                ),
            ],
        ),
    )
    @commands.defer()
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    @vbu.checks.is_config_set("api_keys", "wolfram")
    async def wolfram(self, ctx: vbu.Context, *, search: str):
        """
        Send a query to WolframAlpha.
        """

        # Build our request
        params = {
            "input": search,
            "appid": self.bot.config['api_keys']['wolfram'],
            "format": "image",
            "output": "json",
        }
        headers = {
            "User-Agent": self.bot.user_agent,
        }

        # Send our request
        async with self.bot.session.get("https://api.wolframalpha.com/v2/query", params=params, headers=headers) as r:
            data = json.loads(await r.text())

        # Send output
        try:
            pod = data['queryresult']['pods'][1]
            embed = vbu.Embed(
                title=pod['title'],
                use_random_colour=True,
            ).set_image(
                url=pod['subpods'][0]['img']['src'],
            )
            return await ctx.send(embed=embed)
        except (KeyError, IndexError):
            return await ctx.send("No results for that query!")


def setup(bot: vbu.Bot):
    x = WolframAlpha(bot)
    bot.add_cog(x)
