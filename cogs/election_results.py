import math
from datetime import datetime as dt

import discord
from discord.ext import tasks
import voxelbotutils as utils


HEADERS_BLOCK = """Host: www.politico.com\nUser-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:83.0) Gecko/20100101 Firefox/83.0\nAccept: */*\nAccept-Language: en-US,en;q=0.5\nAccept-Encoding: gzip, deflate, br\nReferer: https://www.politico.com/2020-election/results/president/\nAccess-Control-Allow-Origin: *\nContent-Type: application/json\nSec-GPC: 1\nPragma: no-cache\nCache-Control: no-cache\nTE: Trailers"""
HEADERS = {i.split(':', 1)[0].strip():i.split(':', 1)[1].strip() for i in HEADERS_BLOCK.split('\n')}


class ElectionResults(utils.Cog):

    def __init__(self, bot):
        super().__init__(bot)
        self.message = None
        self.state_fips = None
        self.candidates = None
        self.message_updater.start()

    def cog_unload(self):
        self.message_updater.cancel()

    async def get_messages(self) -> discord.Message:
        if self.message is not None:
            return self.message
        m = await self.bot.get_channel(773014123168006225).fetch_message(773014237487693874)
        n = await self.bot.get_channel(773014123168006225).fetch_message(773366693430427668)
        self.message = (m, n)
        return self.message

    async def get_state_fips(self) -> dict:
        if self.state_fips is not None:
            return self.state_fips
        async with self.bot.session.get("https://www.politico.com/interactives/apps/kitchensink/1MtjbXoHsK1S/data.json", headers=HEADERS) as r:
            data = await r.json()
        f = {}
        for row in data['content']['States']:
            f[row['stateFips']] = row['state']
        self.state_fips = f
        return self.state_fips

    async def get_candidates(self) -> dict:
        if self.candidates is not None:
            return self.candidates
        async with self.bot.session.get("https://www.politico.com/2020-national-metadata/potus.meta.json", headers=HEADERS) as r:
            data = await r.json()
        f = {}
        for row in data:
            for candidate in row['candidates']:
                f[candidate['candidateID']] = (candidate['fullName'], candidate['party'].upper())
        self.candidates = f
        return self.candidates

    @tasks.loop(seconds=30)
    async def message_updater(self):

        # Get data
        async with self.bot.session.get("https://www.politico.com/2020-national-results/balance-of-power.json", headers=HEADERS) as r:
            data = await r.json()

        # Make embed
        EXCLAIM = "\N{WHITE EXCLAMATION MARK ORNAMENT}"
        with utils.Embed() as embed:
            embed.title = "The US Election Results - Live Updating"

            # Add presidential votes
            dem = data['president']['called-d']
            dem_percentage = dem * 100 / sum(data['president'].values())
            rep = data['president']['called-r']
            rep_percentage = rep * 100 / sum(data['president'].values())
            majority = math.ceil((sum(data['president'].values()) / 2) + 0.1)
            embed.add_field(
                "Presidential Votes", (
                    f"\N{LARGE BLUE CIRCLE} (`JB`) **{dem} votes** ({dem_percentage:.1f}% of votes) {EXCLAIM if dem > rep else ''}\n"
                    f"\N{LARGE RED CIRCLE} (`DT`) **{rep} votes** ({rep_percentage:.1f}% of votes){EXCLAIM if rep > dem else ''}\n"
                    f"({dem + rep} Electoral College votes counted of {sum(data['president'].values())} votes total, {majority} needed for a majority)\n"
                ),
                inline=False,
            )
            embed.colour = int(format(int(255 * (rep_percentage or 50) / 100), '02X') + '00' + format(int(255 * (dem_percentage or 50) / 100), '02X'), 16)

            # Add senate seats
            dem = data['senate']['called-d'] + data['senate']['seated-d']
            dem_percentage = dem * 100 / sum(data['senate'].values())
            rep = data['senate']['called-r'] + data['senate']['seated-r']
            rep_percentage = rep * 100 / sum(data['senate'].values())
            majority = math.ceil((sum(data['senate'].values()) / 2) + 0.1)
            embed.add_field(
                "Senate Seats", (
                    f"\N{LARGE BLUE CIRCLE} (`DEM`) **{dem} seats** ({dem_percentage:.1f}% of seats) {EXCLAIM if dem > rep else ''}\n"
                    f"\N{LARGE RED CIRCLE} (`REP`) **{rep} seats** ({rep_percentage:.1f}% of seats){EXCLAIM if rep > dem else ''}\n"
                    f"({dem + rep} seats filled of {sum(data['senate'].values())} seats total, {majority} needed for a majority)\n"
                ),
                inline=False,
            )

            # Add house seats
            dem = data['house']['called-d']
            dem_percentage = dem * 100 / sum(data['house'].values())
            rep = data['house']['called-r']
            rep_percentage = rep * 100 / sum(data['house'].values())
            majority = math.ceil((sum(data['house'].values()) / 2) + 0.1)
            embed.add_field(
                "House Seats", (
                    f"\N{LARGE BLUE CIRCLE} (`DEM`) **{dem} seats** ({dem_percentage:.1f}% of seats) {EXCLAIM if dem > rep else ''}\n"
                    f"\N{LARGE RED CIRCLE} (`REP`) **{rep} seats** ({rep_percentage:.1f}% of seats){EXCLAIM if rep > dem else ''}\n"
                    f"({dem + rep} seats filled of {sum(data['house'].values())} seats total, {majority} needed for a majority)\n"
                ),
                inline=False,
            )

            # Add winners
            async with self.bot.session.get("https://www.politico.com/2020-national-results/president-overall.json", headers=HEADERS) as r:
                data = await r.json()
            stateEmbed = utils.Embed(title="Votes By State")
            state_fips = await self.get_state_fips()
            candidates = await self.get_candidates()
            for state in data['races']:
                if not any([i['winner'] for i in state['candidates']]):
                    # overall_content.append(f"**{state_fips.get(state['stateFips'])}** - No called winner")
                    continue
                win_string_list = []
                for c in state['candidates']:
                    if c['vote'] == 0:
                        continue
                    candy = candidates.get(c['candidateID'], ('Unknown', '???'))
                    win_string = f"`{candy[1]}` - {c['vote']} votes"
                    if c['winner']:
                        win_string_list.insert(0, win_string + ' (winner)')
                    else:
                        win_string_list.append(win_string)
                if not win_string_list:
                    continue
                stateEmbed.add_field(state_fips.get(state['stateFips']), '\n'.join(win_string_list), inline=False)

            # And stuff here
            embed.timestamp = dt.utcnow()
            embed.set_footer(text="Provided by Politico.com")

        # And edit
        m, n = await self.get_messages()
        try:
            await m.edit(content=None, embed=stateEmbed)
        except discord.HTTPException:
            pass
        try:
            await n.edit(content=None, embed=embed)
        except discord.HTTPException:
            pass


def setup(bot):
    x = ElectionResults(bot)
    bot.add_cog(x)
