import typing

from bs4 import BeautifulSoup
from discord.ext import commands

from cogs import utils


class RollercoasterData(utils.Cog):

    HEADERS = {
        "User-Agent": "ApplePy/0.0.1 callum@voxelfox.co.uk"
    }
    BASE = "https://rcdb.com/r.htm"

    @staticmethod
    def get_data_from_search(soup) -> dict:
        """Parse the data from a search and return it in a dictionary"""

        q = soup.find(class_="rer").find("table")
        w = q.find_all("td")
        data = {}
        for index, i in enumerate(w[::7]):
            base = index * 7
            item_id = int(''.join([z for z in list(w[base + 1].children)[0]['href'] if z.isdigit()]))
            x = []
            for o in range(5):
                x.append(list(w[base + 1 + o].children)[0].text)
            name, park, coaster_type, design, status = x
            data[item_id] = {"name": name, "park": park, "type": coaster_type, "design": design, "status": status}
        return data

    @commands.command(cls=utils.Command)
    async def coaster(self, ctx:utils.Context, *, name:typing.Union[int, str]):
        """Finds you the data of a rollercoaster"""

        if isinstance(name, int):
            return await self.coaster_data(ctx, int(name))
        return await self.coaster_search(ctx, name)

    async def coaster_data(self, ctx:utils.Context, coaster_id:int):
        """Get data for a specific coaster"""

        # Grab page data
        async with self.bot.session.get(f"https://rcdb.com/{coaster_id}.htm", headers=self.HEADERS) as r:
            text = await r.text()

        # Get features
        soup = BeautifulSoup(text, "html.parser")
        data = soup.find(class_="stat-tbl")
        x = data.find("tbody")
        v = []
        while True:
            y = list(x)
            for i in y:
                if isinstance(i, str):
                    v.append(i)
                elif i.name == 'span':
                    v.append(i.text)
            try:
                x = y[-1].children
            except (IndexError, AttributeError):
                break
        b = []
        continue_next = False
        for index, i in enumerate(v):
            if continue_next:
                continue_next = False
                continue
            if i.strip().lower() == 'elements':
                break
            try:
                if v[index + 1].strip() in ['ft', 'mph', 'ft tall', 'ft long', '°']:
                    b.append(f"{i}{v[index + 1].strip()}")
                    continue_next = True
                else:
                    b.append(i)
            except IndexError:
                b.append(i)
        features = {}
        for index, i in enumerate(b[::2]):
            try:
                features[i] = b[(index * 2) + 1]
            except IndexError:
                features = {}
                break
        title = soup.title.text
        image = "https://rcdb.com" + soup.find(id="opfAnchor")['data-url']

        # Wew that took a while - let's make that into an embed now
        with utils.Embed(use_random_colour=True) as embed:
            embed.set_author(name=title, url=r.url)
            embed.set_image(image)
            for i, o in features.items():
                embed.add_field(i, o, True)
        await ctx.send(embed=embed)

    async def coaster_search(self, ctx, name:str):
        params = {
            "nc": name,
            "ot": 2
        }
        async with self.bot.session.get(self.BASE, params=params, headers=self.HEADERS) as r:
            text = await r.text()
        soup = BeautifulSoup(text, "html.parser")
        data = self.get_data_from_search(soup)
        if len(data) == 1:
            return await self.coaster_data(ctx, list(data.keys())[0])
        if len(data) == 0:
            return await ctx.send("No results found.")
        with utils.Embed(use_random_colour=True) as embed:
            for i, d in data.items():
                embed.add_field(i, f"{d['name']}\n{d['park']}")
        await ctx.send(embed=embed)


def setup(bot:utils.Bot):
    x = RollercoasterData(bot)
    bot.add_cog(x)
