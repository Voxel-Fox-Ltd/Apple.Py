from datetime import datetime as dt

from discord.ext import tasks

from cogs import utils


class MinecraftData(utils.Cog):

    # https://mcapi.us/server/status?ip=149.202.84.162&port=25588
    MINECRAFT_API = "https://mcapi.us/server/status"
    SERVER_IP = "149.202.84.162"
    SERVER_PORT = 25588
    MINECRAFT_MESSAGE = (716321756171862048, 721771100790325321)  # ChannelID, MessageID

    def __init__(self, bot:utils.Bot):
        super().__init__(bot)
        self.server_status_update.start()

    def cog_unload(self):
        self.server_status_update.cancel()

    @tasks.loop(minutes=10)
    async def server_status_update(self):
        """Updates the Minecraft status message"""

        # Get message
        channel = self.bot.get_channel(self.MINECRAFT_MESSAGE[0])
        message = await channel.fetch_message(self.MINECRAFT_MESSAGE[1])

        # Get data
        async with self.bot.session.get(self.MINECRAFT_API, params={"ip": self.SERVER_IP, "port": self.SERVER_PORT}) as r:
            data = await r.json()

        # Create embed
        with utils.Embed() as embed:
            embed.colour = 0x00ff00 if data['online'] else 0xff0000
            embed.title = f"{self.SERVER_IP}:{self.SERVER_PORT}"
            embed.description = f"Currently running {data['server']['name']}"
            if data['players']['now'] > 0:
                embed.add_field("Currently Online", f"{data['players']['now']}/{data['players']['max']}\n{', '.join(data['players']['list'])}", inline=True)
            else:
                embed.add_field("Currently Online", f"{data['players']['now']}/{data['players']['max']}", inline=True)
            embed.add_field("Uptime", utils.TimeValue(data['duration'] / 1000).clean_spaced)
            embed.timestamp = dt.utcnow()
            embed.set_footer(text="Last updated")
        await message.edit(content=None, embed=embed)

    @server_status_update.before_loop
    async def before_server_status_update(self):
        await self.bot.wait_until_ready()


def setup(bot:utils.Bot):
    x = MinecraftData(bot)
    bot.add_cog(x)
