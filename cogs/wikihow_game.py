import re as regex
import random

from discord.ext import commands
import voxelbotutils as utils


class WikihowGame(utils.Cog):

    SLUG_URL = "https://raw.githubusercontent.com/AhoyLemon/damn.dog/9144c63f8695f6859e91fa57ac1b4ae3003f612b/js/partials/_drawings.js"
    IMAGE_DIRECTORY = "https://raw.githubusercontent.com/AhoyLemon/damn.dog/gh-pages/img/pics/"
    SLUG_REGEX = regex.compile(r"slug: \"(.+)\"")

    def __init__(self, bot:utils.Bot):
        super().__init__(bot)
        self.possible_images = None

    async def load_images(self):
        """Loads images into the cache"""

        async with self.bot.session.get(self.SLUG_URL) as r:
            data = await r.text()
        self.possible_images = [i.group(1) for i in self.SLUG_REGEX.finditer(data, regex.MULTILINE)]

    @utils.command()
    async def wikihow(self, ctx:utils.Context):
        """That classic ol wikihow game"""

        if self.possible_images is None:
            await self.load_images()
        choices = random.choices(self.possible_images, k=4)
        chosen_image = choices[0]
        random.shuffle(choices)
        with utils.Embed(use_random_colour=True) as embed:
            embed.set_image(url=self.IMAGE_DIRECTORY + chosen_image.lower() + '.jpg')
            # await ctx.send(self.IMAGE_DIRECTORY + chosen_image.lower() + '.jpg')
            embed.description = ''.join((
                "1\N{COMBINING ENCLOSING KEYCAP} How to... {0}\n".format(choices[0].lower().replace('-', ' ')),
                "2\N{COMBINING ENCLOSING KEYCAP} How to... {0}\n".format(choices[1].lower().replace('-', ' ')),
                "3\N{COMBINING ENCLOSING KEYCAP} How to... {0}\n".format(choices[2].lower().replace('-', ' ')),
                "4\N{COMBINING ENCLOSING KEYCAP} How to... {0}\n".format(choices[3].lower().replace('-', ' ')),
            ))
        m = await ctx.send(embed=embed)
        for e in ["1\N{COMBINING ENCLOSING KEYCAP}", "2\N{COMBINING ENCLOSING KEYCAP}", "3\N{COMBINING ENCLOSING KEYCAP}", "4\N{COMBINING ENCLOSING KEYCAP}"]:
            await m.add_reaction(e)


def setup(bot:utils.Bot):
    x = WikihowGame(bot)
    bot.add_cog(x)
