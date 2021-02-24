import re
import typing
import random
from urllib.parse import quote

from discord.ext import commands
import voxelbotutils as utils


class DNDCommands(utils.Cog):

    DICE_REGEX = re.compile(r"^(?P<count>\d+)?[dD](?P<type>\d+) *(?P<modifier>(?P<modifier_parity>[+-]) *(?P<modifier_amount>\d+))?$")

    @utils.command(aliases=['roll'])
    @commands.bot_has_permissions(send_messages=True)
    async def dice(self, ctx:utils.Context, *, dice:str=None):
        """
        Rolls a dice for you.
        """

        # Validate the dice
        if not dice:
            raise utils.errors.MissingRequiredArgumentString(dice)
        match = self.DICE_REGEX.search(dice)
        if not match:
            raise commands.BadArgument(f"Your dice was not in the format `AdB+C`.")

        # Roll em
        dice_count = int(match.group("count") or 1)
        dice_type = int(match.group("type"))
        modifier = int((match.group("modifier") or "+0").replace(" ", ""))
        rolls = [random.randint(1, dice_type) for _ in range(dice_count)]
        total = sum(rolls) + modifier

        # Output formatted
        if dice_count > 1:
            return await ctx.send(f"Total **{total}**\n({', '.join([str(i) for i in rolls])}) = {sum(rolls)}")
        return await ctx.send(f"Total **{total}**")

    async def send_web_request(self, resource:str, item:str) -> typing.Optional[dict]:
        """
        Send a web request to the dnd5eapi website.
        """

        url = f"https://www.dnd5eapi.co/api/{resource}/{quote(item.lower().replace(' ', '-'))}/"
        headers = {"User-Agent": self.bot.user_agent}
        async with self.bot.session.get(url, headers=headers) as r:
            v = await r.json()
        if v.get("error"):
            return None
        return v

    @utils.group(name="d&d", aliases=["dnd"])
    @commands.bot_has_permissions(send_messages=True)
    async def dnd(self, ctx:utils.Context):
        """
        The parent group for the D&D commands.
        """

        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @dnd.command(name="spell", aliases=["spells"])
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def dnd_spell(self, ctx:utils.Context, *, spell_name:str):
        """
        Gives you information on a D&D spell.
        """

        async with ctx.typing():
            data = await self.send_web_request("spells", spell_name)
        if not data:
            return await ctx.send("I couldn't find any information for that spell.")
        embed = utils.Embed(
            use_random_colour=True,
            title=data['name'],
            description=data['desc'][0],
        ).add_field(
            "Casting Time", data['casting_time'],
        ).add_field(
            "Range", data['range'],
        ).add_field(
            "Components", ', '.join(data['components']),
        ).add_field(
            "Material", data.get('material', 'N/A'),
        ).add_field(
            "Duration", data['duration'],
        ).add_field(
            "Classes", ', '.join([i['name'] for i in data['classes']]),
        ).add_field(
            "Ritual", data['ritual'],
        ).add_field(
            "Concentration", data['concentration'],
        )
        if data.get('higher_level'):
            embed.add_field(
                "Higher Level", "\n".join(data['higher_level']), inline=False,
            )
        elif data.get('damage'):
            text = ""
            damage_type = data['damage']['damage_type']['name'].lower()
            if data['damage'].get('damage_at_character_level'):
                text += "\nCharacter level " + ", ".join([f"{i}: {o}" for i, o in data['damage']['damage_at_character_level'].items()])
            if data['damage'].get('damage_at_slot_level'):
                text += "\nSlot level " + ", ".join([f"{i}: {o}" for i, o in data['damage']['damage_at_slot_level'].items()])
            embed.add_field(
                "Damage", text.strip(), inline=False,
            )
        return await ctx.send(embed=embed)


def setup(bot:utils.Bot):
    x = DNDCommands(bot)
    bot.add_cog(x)
