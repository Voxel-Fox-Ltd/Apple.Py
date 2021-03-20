import json
from pathlib import Path
import typing

import voxelbotutils as utils
import aiohttp


API_BASE_URL = 'https://secure.runescape.com/m=itemdb_oldschool/api/'
ITEM_IDS_PATH = Path().parent.joinpath('config').joinpath('osrs-item-ids.json')


class RunescapeCommands(utils.Cog):

    def __init__(self, bot):
        super().__init__(bot)
        with open(ITEM_IDS_PATH) as item_ids_file:
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

    async def get_item_value_by_id(self, item_id:int, return_int:bool=True) -> typing.Union[int, str]:
        """
        Get the value of an item given its Runescape ID.
        """

        # Make sure an item ID was passed
        if item_id is None:
            return 1

        # Send our web request
        url = API_BASE_URL + 'catalogue/detail.json'
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
        value = item['current']['price']
        if return_int:
            if isinstance(value, str):
                value = self.rs_notation_to_int(value)
        else:
            value = str(value)

        return value

    @utils.command(aliases=['ge'])
    async def grandexchange(self, ctx, rs_notation:typing.Optional[bool]=True, *, item:str):
        """
        Get the value of an item on the grand exchange (OSRS).
        """

        item = item.capitalize()
        item_id = self.item_ids.get(item)
        if item_id:
            try:
                item_value = await self.get_item_value_by_id(item_id, return_int=not rs_notation)
            except aiohttp.ClientConnectorError:
                return await ctx.send('Error connecting to runescape API.')
            # todo: make into a fancy embed or something, use the icon given by the API
            return await ctx.send(item_value)
        return await ctx.send('Item not found')


def setup(bot:utils.Bot):
    x = RunescapeCommands(bot)
    bot.add_cog(x)
