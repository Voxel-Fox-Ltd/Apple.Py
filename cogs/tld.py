import re as regex
import random

from discord.ext import commands
import voxelbotutils as utils


class tld(utils.Cog):

    TLD_URL = "https://data.iana.org/TLD/tlds-alpha-by-domain.txt"

    def __init__(self, bot:utils.Bot):
        super().__init__(bot)
        self.tlds = None

    async def load_tlds(self):
        """Loads tlds into the cache"""

        async with self.bot.session.get(self.SLUG_URL) as r:
            data = await r.text()
        self.tld_list = data.split("\n")


    @utils.group()
    async def tlds(self, ctx):
        """
        Get some data from the docs.
        """

        pass

    @tlds.command()
    async def random(self, ctx:utils.Context, domain:str=None):
        """Get a random tld"""

        if self.tld_list is None:
            await self.load_tlds()
        tld = random.choice(self.tld_list)
        if domain is None:
            await ctx.send(tld)
        else:
            await ctx.send(f"{domain}.{tld}")
        



def setup(bot:utils.Bot):
    x = tld(bot)
    bot.add_cog(x)
