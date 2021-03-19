import json
from pathlib import Path

import voxelbotutils as utils
import aiohttp


API_BASE_URL = 'https://secure.runescape.com/m=itemdb_oldschool/api/'
ITEM_IDS_PATH = Path().parent.joinpath('config').joinpath('osrs-item-ids.json')


class RunescapeCommands(utils.Cog):
    # https://pastebin.com/raw/LhxJ7GRG (parsed and modified)
    def __init__(self, bot):
        super().__init__(bot)
        with open(ITEM_IDS_PATH) as item_ids_file:
            self.item_ids = json.load(item_ids_file)

    # https://github.com/JMcB17/osrs-blast-furnace-calc
    @staticmethod
    def rs_notation_to_int(value_str):
        multipliers = {
            'k': 10 ** 3,
            'm': 10 ** 6,
            'b': 10 ** 9,
        }

        value_str = value_str.replace(',', '')

        for multi in multipliers:
            if value_str.endswith(multi):
                value_str = value_str.rstrip(multi)
                value = int(value_str) * multipliers[multi]
                break
        else:
            value = int(value_str)

        return value

    async def get_item_value_by_id(self, item_id, return_int=True):
        if item_id is None:
            return 1

        url = API_BASE_URL + 'catalogue/detail.json'
        params = {
            'item': item_id
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                item = await response.json()
            # revolver ocelot (revolver ocelot)
            item = item['item']
        value = item['current']['price']
        if return_int:
            if type(value) == str:
                value = self.rs_notation_to_int(value)
        else:
            value = str(value)

        return value

    @utils.command(aliases=['ge'])
    async def grandexchange(self, ctx, item, rs_notation: bool = True):
        """Get the value of an item on the grand exchange (OSRS)."""
        item_id = self.item_ids.get(item)
        if item_id:
            item_value = await self.get_item_value_by_id(item_id, return_int=not rs_notation)
            # todo: make into a fancy embed or something, use the icon given by the API
            return await ctx.send(item_value)
        else:
            return await ctx.send('Item not found')


def setup(bot:utils.Bot):
    x = RunescapeCommands(bot)
    bot.add_cog(x)
