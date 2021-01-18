import random

import voxelbotutils as utils


class TldCommands(utils.Cog):

    TLD_URL = "https://data.iana.org/TLD/tlds-alpha-by-domain.txt"

    def __init__(self, bot:utils.Bot):
        super().__init__(bot)
        self.tld_list = None

    async def load_tlds(self):
        """Loads tlds into the cache"""

        async with self.bot.session.get(self.TLD_URL) as r:
            data = await r.text()
        self.tld_list = data.split("\n")

    
    @utils.group(aliases=['tld'])
    async def tlds(self, ctx):
        """
        Allows some functions on tlds
        """

        pass

    @tlds.command()
    async def random(self, ctx:utils.Context, domain:str=None):
        """Get a random tld"""

        if self.tld_list is None:
            await self.load_tlds()

        tld = random.choice(self.tld_list)
        if not tld.startswith("XN--"):
            if domain is None:
                await ctx.send(tld)
            else:
                await ctx.send(f"`{domain}.{tld.lower()}")

    @tlds.command()
    async def check(self, ctx:utils.Context, tld_check:str=None):
        """Checks if a tld exists"""

        if self.tld_list is None:
            await self.load_tlds()

        tld_check = tld_check.upper()
        if tld_check in self.tld_list:
            await ctx.send(f"Is a tld. (.{tld_check.lower()}) <:tick_filled_yes:784976310366634034>.")
        else:
            await ctx.send(f"Not a tld. (.{tld_check.lower()}) <:tick_filled_no:784976328231223306>.")
    
        



def setup(bot:utils.Bot):
    x = TldCommands(bot)
    bot.add_cog(x)
