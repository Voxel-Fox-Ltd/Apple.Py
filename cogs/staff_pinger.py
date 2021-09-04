import re

import discord
from discord.ext import vbu


CHANNEL_REGEX = re.compile(r"\*\*Channel:\*\* <#(\d+)>", re.MULTILINE | re.DOTALL)


class StaffPinger(vbu.Cog):

    @vbu.Cog.listener()
    async def on_message(self, message):
        """
        Pings the staff members when a report comes through.
        """

        # Reports channel
        if message.channel.id != 709608383216353280:
            return

        # Yags
        if message.author.id != 204255221017214977:
            return

        # Get embeds
        embed = None
        if message.embeds:
            embed = message.embeds[0]
            original_description = embed.description
            match = CHANNEL_REGEX.search(original_description)
            report_channel_id = match.group(1)
            embed.description += (
                f"\n**Timestamp:** {discord.utils.format_dt(message.created_at)}"
                f"\n**Jump URL:** [Click here](https://discord.com/channels/{message.guild.id}/{report_channel_id}/{message.id})"
            )

        # Make components
        components = discord.ui.MessageComponents(
            discord.ui.ActionRow(
                discord.ui.Button(label="Handle report", custom_id="HANDLE_REPORT"),
            ),
        )

        # Repost message
        await message.delete()
        await message.channel.send(
            f"{message.content} <@&480519382699868181> <@&713026585569263637>",
            # f"{message.content}",
            embeds=[embed],
            components=components,
        )

    @vbu.Cog.listener()
    async def on_component_interaction(self, payload: discord.Interaction):
        """
        Handle the "handle report" button being clicked.
        """

        # See if we care about this button
        if payload.component.custom_id != "HANDLE_REPORT":
            return
        self.logger.info("Received report interaction")

        # Sick
        components = payload.message.components
        report_button = components.get_component("HANDLE_REPORT")
        report_button.label = "Report handled"
        report_button.disabled = True
        components.components[0].add_component(
            discord.ui.Button(label=str(payload.user), custom_id="REPORT_HANDLED_BY", disabled=True),
        )

        # Update message
        await payload.response.edit_message(components=components)
        self.logger.info("Updated report message components")


def setup(bot: vbu.Bot):
    x = StaffPinger(bot)
    bot.add_cog(x)
