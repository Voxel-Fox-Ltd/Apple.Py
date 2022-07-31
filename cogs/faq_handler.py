import discord
from discord.ext import commands, vbu


CSUPPORT_MESSAGE = ("\u200b\n" * 30) + """
Please give a detailed report of:
* What you thought would happen vs what actually happened
* How you cause the issue to happen
* Any extra details (like screenshots)

Ping <@&522072743273824262> for a faster response
"""
CSUPPORT_COMPONENTS = discord.ui.MessageComponents(
    discord.ui.ActionRow(
        discord.ui.Button(
            label="FAQs",
            custom_id="FAQ _",
            style=discord.ui.ButtonStyle.primary,
            disabled=True,
        ),
        discord.ui.Button(
            label="Prefix commands don't work",
            custom_id="FAQ 1003306511772168243",
            style=discord.ui.ButtonStyle.secondary,
        ),
    )
)


class FAQHandler(vbu.Cog[vbu.Bot]):

    FAQ_CHANNEL_ID = 689189625356746755
    SUPPORT_CHANNEL_ID = 689189589776203861

    def __init__(self, bot: vbu.Bot):
        super().__init__(bot)
        self.cached_messages = {}

    async def get_output(self, message_id: int) -> dict:
        """
        Get a message from the API or the cache.
        """

        if message_id in self.cached_messages:
            return self.cached_messages[message_id]
        channel = self.bot.get_partial_messageable(self.FAQ_CHANNEL_ID, type=discord.ChannelType.text)
        faq_message: discord.Message = await channel.fetch_message(message_id)
        data = {
            "content": faq_message.content,
            "embeds": faq_message.embeds,
        }
        self.cached_messages[message_id] = data
        return data

    @commands.command(hidden=True)
    async def csupport(self, ctx: vbu.Context):
        """
        Post the csupport message wew.
        """

        if ctx.channel.id != self.SUPPORT_CHANNEL_ID:
            return
        await ctx.send(
            CSUPPORT_MESSAGE,
            components=CSUPPORT_COMPONENTS,
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @vbu.Cog.listener()
    async def on_component_interaction(self, payload: discord.Interaction):
        """
        See if an FAQ component was clicked.
        """

        if not payload.custom_id.startswith("FAQ"):
            return
        _, asking_for = payload.custom_id.split(" ")
        await payload.response.defer(ephemeral=True)
        data = await self.get_output(int(asking_for))
        return await payload.followup.send(**data, ephemeral=True)


def setup(bot: vbu.Bot):
    x = FAQHandler(bot)
    bot.add_cog(x)
