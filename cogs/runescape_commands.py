import json
import random
import typing
from pathlib import Path

import discord
from discord.ext import commands, vbu


API_BASE_URL = 'https://secure.runescape.com/m=itemdb_oldschool/'
MEMBERS_MAPPING = {
    'true': 'Yes',
    'false': 'No',
}


class RunescapeCommands(vbu.Cog):

    def __init__(self, bot):
        super().__init__(bot)
        self.item_ids_path = (
            Path()
            .parent
            .joinpath('config')
            .joinpath('osrs-item-ids.json')
        )
        with open(self.item_ids_path) as item_ids_file:
            self.item_ids = json.load(item_ids_file)

    @staticmethod
    def rs_notation_to_int(value_str: str) -> int:
        """
        Change a value string ("1.2m") into an int (1200000)
        https://github.com/JMcB17/osrs-blast-furnace-calc
        """

        multipliers = {
            'k': 10 ** 3,
            'm': 10 ** 6,
            'b': 10 ** 9,
        }
        value_str = value_str.replace(',', '').strip()

        for multi, value in multipliers.items():
            if value_str.endswith(multi):
                value_str = value_str.rstrip(multi)
                value = int(float(value_str) * value)
                break
        else:
            value = int(value_str)
        return value

    async def get_item_details_by_id(self, item_id: int) -> dict:
        """
        Return the JSON response from the rs API given an item's Runescape ID.
        """

        # Send our web request
        url = API_BASE_URL + 'api/catalogue/detail.json'
        params = {
            'item': item_id,
        }
        headers = {
            "User-Agent": self.bot.user_agent,
        }
        resp = await self.bot.session.get(url, params=params, headers=headers)
        # The Runescape API doesn't set a json header, so aiohttp complains
        # about it. We can just say to not check the content type.
        item = await resp.json(content_type=None)
        return item['item']

    async def parse_item_value(
            self,
            item: dict,
            return_int: bool = True) -> int | str:
        """
        Parse the value of an item from the JSON response from the rs API.
        """

        value = item['current']['price']
        if isinstance(value, str):
            value = value.strip()
            if return_int:
                value = self.rs_notation_to_int(value)
        else:
            value = str(value)
        return value

    @commands.command(
        aliases=['ge'],
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="item",
                    description="The item that you want to search.",
                    type=discord.ApplicationCommandOptionType.string,
                ),
            ],
        ),
    )
    async def grandexchange(self, ctx: vbu.Context, *, item: str):
        """
        Get the value of an item on the grand exchange (OSRS).
        """

        if item.lower() in ['random']:
            item_id = random.choice(list(self.item_ids.values()))
        else:
            item = item.capitalize()
            item_id = self.item_ids.get(item)

        if not item_id:
            return await ctx.send('Item not found')

        typing = await ctx.typing().__aenter__()
        item_dict = await self.get_item_details_by_id(item_id)
        item_value = await self.parse_item_value(item_dict, return_int=False)

        name = item_dict['name']
        item_page_url = API_BASE_URL + f"a=373/{name.replace(' ', '+')}/viewitem?obj={item_id}"

        with vbu.Embed() as embed:
            embed.set_author(name=name, url=item_page_url, icon_url=item_dict['icon'])
            embed.set_thumbnail(url=item_dict['icon_large'])
            embed.add_field('Value', f'{item_value} coins', inline=False)
            embed.add_field(f'Examine {name}', item_dict['description'], inline=False)
            embed.add_field('Members', MEMBERS_MAPPING[item_dict['members']], inline=False)

        await typing.__aexit__(None, None, None)

        return await ctx.send(embed=embed)


def setup(bot: vbu.Bot):
    x = RunescapeCommands(bot)
    bot.add_cog(x)
