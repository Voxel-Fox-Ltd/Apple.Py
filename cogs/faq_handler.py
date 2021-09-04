import discord
from discord.ext import commands, vbu


CSUPPORT_MESSAGE = ("\u200b\n" * 28) + """
Please give a detailed report of:
* What you thought would happen vs what actually happened
* How you cause the issue to happen
* Any extra details (like screenshots)

Ping `@Support Team` for a faster response
"""
CSUPPORT_COMPONENTS = discord.ui.MessageComponents(
    discord.ui.ActionRow(
        discord.ui.Button(label="See the FAQs", custom_id="FAQ")
    )
)
FAQ_COMPONENTS = discord.ui.MessageComponents(
    discord.ui.ActionRow(
        discord.ui.Button(label="MarriageBot FAQs ->", custom_id="_", disabled=True),
        discord.ui.Button(label="I can't disown my child", custom_id="FAQ CANT_DISOWN", style=discord.ui.ButtonStyle.secondary),
        discord.ui.Button(label="None of the commands work", custom_id="FAQ NO_COMMANDS_WORK", style=discord.ui.ButtonStyle.secondary),
        discord.ui.Button(label="Gold doesn't have my family tree", custom_id="FAQ COPY_FAMILY_TO_GOLD", style=discord.ui.ButtonStyle.secondary),
    ),
)


class FAQHandler(vbu.Cog):

    NO_COMMANDS_WORK = 729049284129062932  # setprefix
    CANT_DISOWN = 729049343260229652  # useid
    COPY_FAMILY_TO_GOLD = 729050839502553089
    NEED_TO_BE_MODERATOR = 729051025184653413  # create a role called marriagebot moderator

    FAQ_CHANNEL_ID = 689189625356746755
    SUPPORT_CHANNEL_ID = 689189589776203861

    def __init__(self, bot: vbu.Bot):
        super().__init__(bot)
        self.cached_messages = {}

    async def get_output(self, key: str) -> dict:
        """
        Get a message from the API or the cache.
        """

        if key in self.cached_messages:
            return self.cached_messages[key]
        message_id: int = getattr(self, key)
        faq_message: discord.Message = await self.bot.get_channel(self.FAQ_CHANNEL_ID).fetch_message(message_id)
        data = {
            "content": faq_message.content,
            "embeds": faq_message.embeds,
        }
        self.cached_messages[key] = data
        return data

    @commands.command(hidden=True)
    async def csupport(self, ctx: vbu.Context):
        """
        Post the csupport message wew.
        """

        if ctx.channel.id != self.SUPPORT_CHANNEL_ID:
            return
        await ctx.send(CSUPPORT_MESSAGE, components=CSUPPORT_COMPONENTS)

    @commands.command(hidden=True)
    async def faq(self, ctx: vbu.Context):
        """
        Post the FAQ message for people who don't want to look in the support channel.
        """

        return await ctx.send("Click a button to see the FAQ response.", components=FAQ_COMPONENTS)

    @vbu.Cog.listener()
    async def on_component_interaction(self, payload):
        """
        See if an FAQ component was clicked.
        """

        if not payload.component.custom_id.startswith("FAQ"):
            return
        try:
            _, asking_for = payload.component.custom_id.split(" ")
        except ValueError:
            return await payload.respond("Click a button to see the FAQ response.", components=FAQ_COMPONENTS, ephemeral=True)
        data = await self.get_output(asking_for)
        return await payload.respond(**data, ephemeral=True)


def setup(bot: vbu.Bot):
    x = FAQHandler(bot)
    bot.add_cog(x)
