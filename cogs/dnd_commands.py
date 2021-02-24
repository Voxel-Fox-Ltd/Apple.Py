import typing
from urllib.parse import quote

from discord.ext import commands
import voxelbotutils as utils


class DNDCommands(utils.Cog):

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
        if data.get('damage'):
            damage_type = data['damage']['damage_type']['name'].lower()
            if data['damage'].get('damage_at_character_level'):
                embed.add_field(
                    "Damage", "\n".join([f"Character level {i}: {o} {damage_type} damage" for i, o in data['damage']['damage_at_character_level'].items()]),
                )
            if data['damage'].get('damage_at_slot_level'):
                embed.add_field(
                    "Damage", "\n".join([f"Slot level {i}: {o} {damage_type} damage" for i, o in data['damage']['damage_at_slot_level'].items()]),
                )
        return await ctx.send(embed=embed)


def setup(bot:utils.Bot):
    x = DNDCommands(bot)
    bot.add_cog(x)
