import discord
import voxelbotutils as vbu


CSUPPORT_MESSAGE = """\u200b\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n
Please give a detailed report of:
* What you thought would happen vs what actually happened
* How you cause the issue to happen
* Any extra details (like screenshots)

Ping `@Support Team` for a faster response
"""
COMPONENTS = vbu.MessageComponents(
    vbu.ActionRow(
        vbu.Button("I can't disown my child", "FAQ CANT_DISOWN"),
        vbu.Button("None of the commands work", "FAQ NO_COMMANDS_WORK"),
        vbu.Button("Gold doesn't have my family tree", "FAQ COPY_FAMILY_TO_GOLD"),
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

    @vbu.command(hidden=True)
    async def csupport(self, ctx: vbu.Context):
        """
        Post the csupport message wew.
        """

        if ctx.channel.id != self.SUPPORT_CHANNEL_ID:
            return
        await ctx.send(CSUPPORT_MESSAGE, components=COMPONENTS)

    @vbu.Cog.listener()
    async def on_component_interaction(self, payload):
        """
        See if an FAQ component was clicked.
        """

        if not payload.component.custom_id.startswith("FAQ "):
            return
        _, asking_for = payload.component.custom_id.split(" ")
        data = await self.get_output(asking_for)
        return await payload.respond(**data, ephemeral=True)


def setup(bot: vbu.Bot):
    x = FAQHandler(bot)
    bot.add_cog(x)
