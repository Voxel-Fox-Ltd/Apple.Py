from typing import Union
import random

import discord
from discord.ext import commands, vbu


class MiscCommands(vbu.Cog):

    @commands.command(application_command_meta=commands.ApplicationCommandMeta())
    @commands.bot_has_permissions(send_messages=True)
    async def coinflip(self, ctx: vbu.Context):
        """
        Flips a coin.
        """

        coin = ["Heads", "Tails"]
        return await ctx.send(random.choice(coin))

    @commands.command(
        aliases=['color'],
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="colour",
                    description="The colour that you want to post.",
                    type=discord.ApplicationCommandOptionType.string,
                ),
            ],
        ),
    )
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def colour(
            self,
            ctx: vbu.Context,
            *,
            colour: Union[vbu.converters.ColourConverter, discord.Colour, discord.Role, discord.Member],
            ):
        """
        Get you a colour.
        """

        hex_colour: int = 0
        if isinstance(colour, (discord.Role, discord.Member)):
            hex_colour = colour.colour.value
        elif isinstance(colour, discord.Colour):
            hex_colour = colour.value
        elif isinstance(colour, int):
            hex_colour = colour
        elif isinstance(colour, str):
            hex_colour = int(colour, 16)
        hex_colour = colour.value
        with vbu.Embed(colour=hex_colour, title=f"#{hex_colour:0>6X}") as embed:
            embed.set_image(url=f"https://voxelfox.co.uk/colour?hex={hex_colour:0>6X}")
        await ctx.send(embed=embed)


def setup(bot: vbu.Bot):
    x = MiscCommands(bot)
    bot.add_cog(x)
