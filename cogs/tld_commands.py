import random

import voxelbotutils as utils


class TLDCommands(utils.Cog):

    TLD_URL = "https://data.iana.org/TLD/tlds-alpha-by-domain.txt"

    def __init__(self, bot:utils.Bot):
        super().__init__(bot)
        self.tld_list = None

    async def get_tlds(self):
        """
        Loads TLDs into the cache.
        """

        if self.tld_list:
            return self.tld_list
        headers = {"User-Agent": self.bot.user_agent}
        async with self.bot.session.get(self.TLD_URL, headers=headers) as r:
            data = await r.text()
        self.tld_list = [i for i in data.strip().split("\n") if not i.startswith(("# ", ".XN--"))]
        return self.tld_list

    @utils.group(aliases=['tld'])
    async def tlds(self, ctx):
        """
        The parent group for the TLD commands.
        """

        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @tlds.command()
    async def random(self, ctx:utils.Context, domain:str=None):
        """
        Get a random TLD.
        """

        tld = random.choice(await self.get_tlds())
        if not tld.startswith("XN--"):
            if domain is None:
                await ctx.send(f"`{tld.lower()}`")
            else:
                await ctx.send(f"`{domain}.{tld.lower()}`")

    @tlds.command()
    async def check(self, ctx:utils.Context, tld_check:str=None):
        """
        Checks if a TLD exists.
        """

        tld_check = tld_check.upper()
        if tld_check in await self.get_tlds():
            await ctx.send(f"Is a TLD. (`.{tld_check.lower()}`) \N{WHITE HEAVY CHECK MARK}.")
        else:
            await ctx.send(f"Not a TLD. (`.{tld_check.lower()}`) \N{CROSS MARK}.")


def setup(bot:utils.Bot):
    x = TLDCommands(bot)
    bot.add_cog(x)
