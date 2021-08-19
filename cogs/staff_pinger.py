import voxelbotutils as vbu


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
        embeds = None
        if message.embeds:
            embeds = message.embeds

        # Make components
        components = vbu.MessageComponents(
            vbu.ActionRow(
                vbu.Button("Handle report", "HANDLE_REPORT"),
            ),
        )

        # Repost message
        await message.delete()
        await message.channel.send(
            f"{message.content} <@&480519382699868181> <@&713026585569263637>",
            embeds=embeds,
            components=components,
        )

    @vbu.Cog.listener()
    async def on_component_interaction(self, payload: vbu.ComponentInteractionPayload):
        """
        Handle the "handle report" button being clicked.
        """

        # See if we care about this button
        if payload.component.custom_id != "HANDLE_REPORT":
            return

        # Sick
        components = payload.message.components
        report_button = components.get_component("HANDLE_REPORT")
        report_button.label = "Report handled"
        report_button.disabled = True
        components.components[0].components[0].add_component(
            vbu.Button(str(payload.user), "REPORT_HANDLED_BY", disabled=True),
        )

        # Update message
        await payload.update_message(components=components)


def setup(bot: vbu.Bot):
    x = StaffPinger(bot)
    bot.add_cog(x)
