import random
from datetime import datetime as dt

from discord.ext import tasks
import voxelbotutils as utils


class VcChatUpdate(utils.Cog):

    NO_MIC_CHANNEL = 646155412692926475
    PART1 = ('voice', 'voiced', 'vocal', 'voiceable', 'vixen', 'vc', 'voie', 'vampire',)
    PART2 = ('chat', 'cat', 'c', 'cats', 'chatting', 'cool', 'xhta',)
    PART3 = ('no', 'n', 'negative', 'nine', 'none',)
    PART4 = ('mic', 'microphone', 'mitchell', 'michelle', 'michael', 'mikey', 'monkey', 'schlopp', 'megan', 'mice', 'micloryphe', 'microwave',)

    def __init__(self, bot:utils.Bot):
        super().__init__(bot)
        self.last_posted_day: int = None
        self.vc_update.start()

    def cog_unload(self):
        self.vc_update.cancel()

    @tasks.loop(seconds=1)
    async def vc_update(self):
        """Check if we should update the channel"""

        # Check if we should update the channel
        now = dt.utcnow()
        if now.day != self.last_posted_day and now.hour == 0:
            self.last_posted_day = now.day
        else:
            return
        self.bot.dispatch("update_voice_vc")

    @utils.Cog.listener("on_update_voice_vc")
    async def change_vc_name(self):
        self.logger.info('VC no mic channel updating...')
        channel = self.bot.get_channel(self.NO_MIC_CHANNEL)
        if channel is None:
            self.logger.warning('VC no mic channel could not be found.')
            return
        await channel.edit(name=f"{random.choice(self.PART1)}-{random.choice(self.PART2)}-{random.choice(self.PART3)}-{random.choice(self.PART4)}")
        await self.logger.info('VC no mic channel has been updated.')


def setup(bot:utils.Bot):
    x = VcChatUpdate(bot)
    bot.add_cog(x)
