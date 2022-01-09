import re
import typing
import random
from urllib.parse import quote
import functools
import operator

import discord
from discord.ext import commands, vbu
from thefuzz import fuzz

from .types.bot import Bot


class _DNDMonsterAction(typing.TypedDict, total=False):
    name: str
    desc: str


class DNDCommands(vbu.Cog[Bot]):

    DICE_REGEX = re.compile(r"^(?P<count>\d+)?[dD](?P<type>\d+) *(?P<modifier>(?P<modifier_parity>[+-]) *(?P<modifier_amount>\d+))?$")
    ATTRIBUTES = {
        "strength": "STR",
        "dexterity": "DEX",
        "constitution": "CON",
        "intelligence": "INT",
        "wisdom": "WIS",
        "charisma": "CHR",
    }

    @commands.command(
        aliases=['roll'],
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="dice",
                    type=discord.ApplicationCommandOptionType.string,
                    description="The die (in form 'XdY+Z', eg '5d6+2') that you want to roll.",
                ),
            ],
        ),
    )
    @commands.bot_has_permissions(send_messages=True)
    async def dice(self, ctx: commands.Context, *, dice: str):
        """
        Rolls a dice for you.
        """

        # Validate the dice
        if not dice:
            raise vbu.errors.MissingRequiredArgumentString(dice)
        match = self.DICE_REGEX.search(dice)
        if not match:
            raise commands.BadArgument("Your dice was not in the format `AdB+C`.")

        # Roll em
        dice_count = int(match.group("count") or 1)
        dice_type = int(match.group("type"))
        modifier = int((match.group("modifier") or "+0").replace(" ", ""))
        rolls = [random.randint(1, dice_type) for _ in range(dice_count)]
        total = sum(rolls) + modifier
        dice_string = f"{dice_count}d{dice_type}{modifier:+}"
        if not modifier:
            dice_string = dice_string[:-2]

        # Get formatted output
        if dice_count > 1 or modifier:
            equals_string = f"{sum(rolls)} {'+' if modifier > 0 else '-'} {abs(modifier)}"
            if modifier:
                text = f"Total **{total:,}** ({dice_string})\n({', '.join([str(i) for i in rolls])}) = {equals_string}"
            else:
                text = f"Total **{total:,}** ({dice_string})\n({', '.join([str(i) for i in rolls])}) = {equals_string}"
        else:
            text = f"Total **{total}** ({dice_string})"

        # And output
        if isinstance(ctx, commands.SlashContext):
            await ctx.interaction.response.send_message(text)
        else:
            await ctx.send(text)

    async def send_web_request(self, resource: str, item: str) -> typing.Optional[dict]:
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

    @staticmethod
    def group_field_descriptions(
            embed: discord.Embed,
            field_name: str,
            input_list: typing.List[_DNDMonsterAction],
            ) -> None:
        """
        Add fields grouped to the embed character limit.
        """

        original_field_name = field_name
        joiner = "\n"
        action_text = [f"**{i['name']}**{joiner}{i['desc']}" for i in input_list]
        add_text = ""
        for text in action_text:
            if len(add_text) + len(text) + 1 > 1024:
                embed.add_field(
                    name=field_name,
                    value=add_text,
                    inline=False,
                )
                field_name = f"{original_field_name} Continued"
                add_text = ""
            add_text += joiner + text
        if add_text:
            embed.add_field(
                name=field_name,
                value=add_text,
                inline=False,
            )

    @commands.group(
        aliases=["d&d"],
        application_command_meta=commands.ApplicationCommandMeta(),
    )
    @commands.bot_has_permissions(send_messages=True)
    async def dnd(self, ctx: commands.Context):
        """
        The parent group for the D&D commands.
        """

        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @dnd.command(
        name="spell",
        aliases=["spells"],
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="spell_name",
                    description="The name of the spell that you want to get the information of.",
                    type=discord.ApplicationCommandOptionType.string,
                    autocomplete=True,
                ),
            ],
        ),
    )
    @commands.defer()
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def dnd_spell(self, ctx: commands.Context, *, spell_name: str):
        """
        Gives you information on a D&D spell.
        """

        # Get our data
        async with ctx.typing():
            data = await self.send_web_request("spells", spell_name)
        if not data:
            return await ctx.send("I couldn't find any information for that spell.")

        # Make an embed
        embed = vbu.Embed(
            use_random_colour=True,
            title=data['name'],
            description=data['desc'][0],
        ).add_field(
            name="Casting Time",
            value=data['casting_time'],
        ).add_field(
            name="Range",
            value=data['range'],
        ).add_field(
            name="Components",
            value=', '.join(data['components']),
        ).add_field(
            name="Material",
            value=data.get('material', 'N/A'),
        ).add_field(
            name="Duration",
            value=data['duration'],
        ).add_field(
            name="Classes",
            value=', '.join([i['name'] for i in data['classes']]),
        ).add_field(
            name="Ritual",
            value=data['ritual'],
        ).add_field(
            name="Concentration",
            value=data['concentration'],
        )
        if data.get('higher_level'):
            embed.add_field(
                name="Higher Level",
                value="\n".join(data['higher_level']), inline=False,
            )
        elif data.get('damage'):
            text = ""
            if data['damage'].get('damage_at_character_level'):
                text += "\nCharacter level " + ", ".join([f"{i}: {o}" for i, o in data['damage']['damage_at_character_level'].items()])
            if data['damage'].get('damage_at_slot_level'):
                text += "\nSlot level " + ", ".join([f"{i}: {o}" for i, o in data['damage']['damage_at_slot_level'].items()])
            embed.add_field(
                name="Damage",
                value=text.strip(),
                inline=False,
            )

        # And send
        return await ctx.send(embed=embed)

    @functools.cached_property
    def all_spells(self) -> typing.List[str]:
        with open("cogs/data/dnd_spells.txt") as a:
            return a.read().strip().split("\n")

    @dnd_spell.autocomplete
    async def dnd_spell_autocomplete(self, ctx: commands.SlashContext, interaction: discord.Interaction[None]):
        """
        Fuzzy match what the user input and the list of all spells.
        """

        # Get what the user gave us
        assert interaction.options is not None
        user_input = interaction.options[0].value

        # Determine what's closest to what they said
        fuzzed = [(i, fuzz.ratio(i, user_input),) for i in self.all_spells]
        fuzzed.sort(key=operator.itemgetter(1), reverse=True)

        # And give them the top results
        await interaction.response.send_autocomplete([
            discord.ApplicationCommandOptionChoice(name=i, value=i)
            for i in fuzzed[:25]
        ])

    @dnd.command(
        name="monster",
        aliases=["monsters"],
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="monster_name",
                    description="The monster that you want to get the information of.",
                    type=discord.ApplicationCommandOptionType.string,
                ),
            ],
        ),
    )
    @commands.defer()
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def dnd_monster(self, ctx: commands.Context, *, monster_name: str):
        """
        Gives you information on a D&D monster.
        """

        # Get our data
        async with ctx.typing():
            data = await self.send_web_request("monsters", monster_name)
        if not data:
            return await ctx.send("I couldn't find any information for that monster.")

        # Make an embed
        embed = vbu.Embed(
            use_random_colour=True,
            title=data['name'],
            description="\n".join([
                f"{data['size'].capitalize()} | {data['type']} | {data['hit_points']:,} ({data['hit_dice']}) HP | {data['xp']:,} XP",
                ", ".join([f"{o} {data[i]}" for i, o in self.ATTRIBUTES.items()]),
            ])
        ).add_field(
            name="Proficiencies",
            value=", ".join([f"{i['proficiency']['name']} {i['value']}" for i in data['proficiencies']]) or "None",
        ).add_field(
            name="Damage Vulnerabilities",
            value="\n".join(data['damage_vulnerabilities']).capitalize() or "None",
        ).add_field(
            name="Damage Resistances",
            value="\n".join(data['damage_resistances']).capitalize() or "None",
        ).add_field(
            name="Damage Immunities",
            value="\n".join(data['damage_immunities']).capitalize() or "None",
        ).add_field(
            name="Condition Immunities",
            value="\n".join([i['name'] for i in data['condition_immunities']]).capitalize() or "None",
        ).add_field(
            name="Senses",
            value="\n".join([f"{i.replace('_', ' ').capitalize()} {o}" for i, o in data['senses'].items()]) or "None",
        )
        self.group_field_descriptions(embed, "Actions", data['actions'])
        self.group_field_descriptions(embed, "Legendary Actions", data.get('legendary_actions', list()))
        if data.get('special_abilities'):
            embed.add_field(
                name="Special Abilities",
                value="\n".join([f"**{i['name']}**\n{i['desc']}" for i in data['special_abilities'] if i['name'] != 'Spellcasting']) or "None",
                inline=False,
            )
        spellcasting = [i for i in data.get('special_abilities', list()) if i['name'] == 'Spellcasting']
        if spellcasting:
            spellcasting = spellcasting[0]
            embed.add_field(
                name="Spellcasting",
                value=spellcasting['desc'].replace('\n\n', '\n'),
                inline=False,
            )

        # And send
        return await ctx.send(embed=embed)

    @dnd.command(
        name="condition",
        aliases=["conditions"],
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="condition_name",
                    description="The condition that you want to get the information of.",
                    type=discord.ApplicationCommandOptionType.string,
                ),
            ],
        ),
    )
    @commands.defer()
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def dnd_condition(self, ctx: commands.Context, *, condition_name: str):
        """
        Gives you information on a D&D condition.
        """

        # Get our data
        async with ctx.typing():
            data = await self.send_web_request("conditions", condition_name)
        if not data:
            return await ctx.send("I couldn't find any information for that condition.")

        # Make an embed
        embed = vbu.Embed(
            use_random_colour=True,
            title=data['name'],
            description="\n".join(data['desc']),
        )

        # And send
        return await ctx.send(embed=embed)

    @dnd.command(
        name="class",
        aliases=["classes"],
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="class_name",
                    description="The class that you want to get the informaton of.",
                    type=discord.ApplicationCommandOptionType.string,
                ),
            ],
        ),
    )
    @commands.defer()
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def dnd_class(self, ctx: commands.Context, *, class_name: str):
        """
        Gives you information on a D&D class.
        """

        # Get our data
        async with ctx.typing():
            data = await self.send_web_request("classes", class_name)
        if not data:
            return await ctx.send("I couldn't find any information for that class.")

        # Make embed
        embed = vbu.Embed(
            use_random_colour=True,
            title=data['name'],
        ).add_field(
            "Proficiencies", ", ".join([i['name'] for i in data['proficiencies']]),
        ).add_field(
            "Saving Throws", ", ".join([i['name'] for i in data['saving_throws']]),
        ).add_field(
            "Starting Equipment", "\n".join([f"{i['quantity']}x {i['equipment']['name']}" for i in data['starting_equipment']]),
        )

        # And send
        return await ctx.send(embed=embed)


def setup(bot: Bot):
    x = DNDCommands(bot)
    bot.add_cog(x)
