import json
from pathlib import Path
import typing

import voxelbotutils as utils
import aiohttp


API_BASE_URL = 'https://secure.runescape.com/m=itemdb_oldschool/'
MEMBERS_MAPPING = {
    'true': 'Yes',
    'false': 'No',
}


class RunescapeCommands(utils.Cog):

    # https://pastebin.com/raw/LhxJ7GRG (parsed and modified)
    def __init__(self, bot):
        super().__init__(bot)
        self.item_ids_path = Path().parent.joinpath('config').joinpath('osrs-item-ids.json')
        with open(self.item_ids_path) as item_ids_file:
            self.item_ids = json.load(item_ids_file)

    @staticmethod
    def rs_notation_to_int(value_str:str) -> int:
        """
        Change a value string ("1.2m") into an int (1200000)
        https://github.com/JMcB17/osrs-blast-furnace-calc
        """

        multipliers = {
            'k': 10 ** 3,
            'm': 10 ** 6,
            'b': 10 ** 9,
        }
        value_str = value_str.replace(',', '')

        for multi, value in multipliers.items():
            if value_str.endswith(multi):
                value_str = value_str.rstrip(multi)
                value = int(value_str) * value
                break
        else:
            value = int(value_str)
        return value

    async def get_item_details_by_id(self, item_id:int) -> dict:
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
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as response:
                # The Runescape API doesn't set a json header, so aiohttp complains about it.
                # We can just say to not check the content type.
                # https://github.com/aio-libs/aiohttp/blob/8c82ba11b9e38851d75476d261a1442402cc7592/aiohttp/web_request.py#L664-L681
                item = await response.json(content_type=None)

        # revolver ocelot (revolver ocelot)
        item = item['item']
        return item

    async def parse_item_value(self, item:dict, return_int:bool=True) -> typing.Union[int, str]:
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

    @utils.command(aliases=['ge'])
    async def grandexchange(self, ctx, item:str, rs_notation:bool=True):
        """
        Get the value of an item on the grand exchange (OSRS).
        """

        item_id = self.item_ids.get(item)
        if item_id:
            item_dict = await self.get_item_details_by_id(item_id)
            item_value = await self.parse_item_value(item_dict, return_int=not rs_notation)

            name = item_dict['name']
            item_page_url = API_BASE_URL + f"a=373/{name.replace(' ', '+')}/viewitem?obj={item_id}"

            with utils.Embed() as embed:
                embed.set_author(name=name, url=item_page_url, icon_url=item_dict['icon'])
                embed.set_thumbnail(url=item_dict['icon_large'])
                embed.add_field('Value', item_value)
                embed.add_field(f'Examine {name}', item_dict['description'])
                embed.add_field('Members', MEMBERS_MAPPING[item_dict['members']])

            return await ctx.send(embed=embed)
        return await ctx.send('Item not found')


def setup(bot:utils.Bot):
    x = RunescapeCommands(bot)
    bot.add_cog(x)
