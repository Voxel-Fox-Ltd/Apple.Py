import discord
from discord.ext import tasks
import voxelbotutils as utils


SUPPORT_GUILD_ID = 830286019520626710
BOT_PICKER_CHANNEL_ID = 830286547247955998
PICKABLE_FAQ_CHANNELS = {
    "<:marriage_bot:643484716607209482>": 830294468929912842,  # MarriageBot Support
    "<:flower:777636276790624256>": 830294484045529140,  # Flower Support
    "<:big_ben:709600097574584420>": 830294528958398464,  # Big Ben Support
    # "\N{HONEY POT}": 830286876182708254,  # Honey Support
    # "\N{DOG FACE}": 830286832964993074,  # Cerberus Support
    "\N{BLACK QUESTION MARK ORNAMENT}": 830546400542589019,  # Other Support
    "\N{SPEECH BALLOON}": 830546422930604072,  # Hang out
}


class SupportFAQHandler(utils.Cog):

    BOT_PICKER_MESSAGE_ID = None

    def __init__(self, bot:utils.Bot):
        super().__init__(bot)
        self.guild_purge_loop.start()

    def cog_unload(self):
        self.guild_purge_loop.cancel()

    @tasks.loop(days=1)
    async def guild_purge_loop(self):
        """
        Automatically purges the support guild.
        """

        await self.bot.get_guild(SUPPORT_GUILD_ID).prune_members(days=7, compute_prune_count=False, reason="Automatic purge event.")

    @guild_purge_loop.before_loop
    async def before_guild_purge_loop(self):
        return await self.bot.wait_until_ready()

    @utils.Cog.listener()
    async def on_raw_reaction_add(self, payload:discord.RawReactionActionEvent):
        """
        Runs the support guild reaction handler.
        """

        # Make sure the guild is right
        if payload.guild_id != SUPPORT_GUILD_ID:
            return
        guild = self.bot.get_guild(SUPPORT_GUILD_ID)
        member = guild.get_member(payload.user_id)
        if member.bot:
            return

        # See if we're looking at the bot picker
        if payload.channel_id == BOT_PICKER_CHANNEL_ID:
            new_channel_id = PICKABLE_FAQ_CHANNELS[str(payload.emoji)]
            new_channel = self.bot.get_channel(new_channel_id)
            await new_channel.set_permissions(member, read_messages=True)
            await (await new_channel.send(member.mention)).delete()  # Ghost ping em
            return

        # We could be looking at an faq channel
        current_channel = self.bot.get_channel(payload.channel_id)
        if current_channel.name == "faqs":
            current_category = current_channel.category
            try:
                new_channel = current_category.channels[int(str(payload.emoji)[0])]  # They gave a number
            except ValueError:
                new_channel_id = PICKABLE_FAQ_CHANNELS["\N{BLACK QUESTION MARK ORNAMENT}"]  # Take them to other support
                new_channel = self.bot.get_channel(new_channel_id)
            await new_channel.set_permissions(member, read_messages=True)
            await (await new_channel.send(member.mention)).delete()  # Ghost ping em
            # await current_channel.set_permissions(member, overwrite=None)
            return

        # It's probably a tick mark
        pass


def setup(bot:utils.Bot):
    x = SupportFAQHandler(bot)
    bot.add_cog(x)
