from typing import cast
import re

import discord
from discord.ext import commands, vbu


class RolePicker(vbu.Cog[vbu.Bot]):

    def get_role_picker_components(self):
        return discord.ui.MessageComponents(
            discord.ui.ActionRow(
                discord.ui.Button(
                    label="Add role",
                    style=discord.ButtonStyle.green,
                    custom_id="NEWROLEPICKER ADDPICKER",
                ),
                discord.ui.Button(
                    label="Remove role",
                    style=discord.ButtonStyle.red,
                    custom_id="NEWROLEPICKER REMOVEPICKER",
                ),
                discord.ui.Button(
                    label="Set content",
                    style=discord.ButtonStyle.secondary,
                    custom_id="NEWROLEPICKER CONTENT",
                ),
                discord.ui.Button(
                    label="Done",
                    style=discord.ButtonStyle.primary,
                    custom_id="NEWROLEPICKER DONE",
                ),
            ),
        )

    @commands.command(
        application_command_meta=commands.ApplicationCommandMeta(
            guild_only=True,
            permissions=discord.Permissions(administrator=True),
        ),
    )
    async def newrolepicker(
            self,
            ctx: vbu.SlashContext):
        """
        Create a new role picker.
        """

        embed = vbu.Embed(
            title="Role Picker Setup",
            use_random_colour=True,
        )
        await ctx.interaction.response.send_message(
            embeds=[embed],
            components=self.get_role_picker_components(),
            ephemeral=True,
        )

    @vbu.Cog.listener("on_component_interaction")
    @vbu.checks.interaction_filter(start="NEWROLEPICKER")
    async def rolepicker_edit(
            self,
            interaction: discord.ComponentInteraction,
            action: str,
            *args):
        """
        Manage the rolepicker edit buttons.
        """

        if action == "ADDPICKER":
            await self.rolemenu_picker(interaction, add=True)
        elif action == "REMOVEPICKER":
            await self.rolemenu_picker(interaction, add=False)
        elif action == "ADD":
            await self.change_roles(interaction, add=True)
        elif action == "REMOVE":
            await self.change_roles(interaction, add=False)
        elif action == "DONE":
            await self.rolemenu_done(interaction)
        elif action == "CONTENT":
            await self.rolemenu_content_spawnmodal(interaction)
        elif action == "ROLE":
            await self.rolepicker_role(interaction, *args)

    async def rolemenu_picker(
            self,
            interaction: discord.ComponentInteraction,
            add: bool):
        """
        Spawns a dropdown for the user to add new roles.
        """

        content = (
            "What role do you want to add?"
            if add
            else "What role do you want to remove?"
        )
        custom_id = "NEWROLEPICKER ADD" if add else "NEWROLEPICKER REMOVE"
        await interaction.response.edit_message(
            content=content,
            components=discord.ui.MessageComponents(
                discord.ui.ActionRow(
                    discord.ui.RoleSelectMenu(
                        custom_id=custom_id,
                    ),
                ),
            ),
        )

    @vbu.Cog.listener("on_modal_submit")
    @vbu.checks.interaction_filter(start="NEWROLEPICKER")
    async def rolemenu_content_modal(
            self,
            interaction: discord.ModalInteraction,
            action: str):
        """
        Manage the rolepicker content modal.
        """

        if action == "SETCONTENT":
            await self.rolemenu_content(interaction)

    async def change_roles(
            self,
            interaction: discord.ComponentInteraction,
            add: bool):
        """
        Update roles available in the embed.
        """

        # Get current embed
        embed = interaction.message.embeds[0]
        try:
            embed_value: str = embed.fields[0].value  # pyright: ignore
        except IndexError:
            embed_value = ""

        # See what the user picked from the dropdown
        role = list(interaction.resolved.roles.values())[0]

        # See if the role is in the current embed values
        if role.mention in embed_value and add is False:
            embed_value = embed_value.replace(role.mention, "")
            embed_value = embed_value.replace("\n\n", "\n")
        elif role.mention not in embed_value and add is True:
            embed_value += f"\n{role.mention}"

        # Edit the embed
        if embed_value.strip():
            try:
                embed.set_field_at(0, name="Roles", value=embed_value.strip())
            except IndexError:
                embed.add_field(name="Roles", value=embed_value.strip())
        else:
            embed.remove_field(0)
        await interaction.response.edit_message(
            content=None,
            embeds=[embed],
            components=self.get_role_picker_components(),
        )

    async def rolemenu_content_spawnmodal(self, interaction: discord.ComponentInteraction):
        """
        Send the user a modal so as to set the content for a rolepicker.
        """

        try:
            current_value = interaction.message.embeds[0].description
            current_value = cast(str | None, current_value)
        except Exception:
            return
        await interaction.response.send_modal(
            discord.ui.Modal(
                title="Set content",
                custom_id="NEWROLEPICKER SETCONTENT",
                components=[
                    discord.ui.ActionRow(
                        discord.ui.InputText(
                            label="Message content",
                            style=discord.TextStyle.long,
                            value=current_value or "",
                        ),
                    ),
                ],
            ),
        )

    async def rolemenu_content(self, interaction: discord.ModalInteraction):
        """
        Set the content of an embed when a modal is submitted.
        """

        # Get current embed
        await interaction.response.defer_update()
        original_message = await interaction.original_message()
        embed = original_message.embeds[0]

        # Change description
        embed.description = (
            interaction
            .components[0]
            .components[0]
            .value
            .strip()
        )
        await original_message.edit(
            embeds=[embed],
        )

    async def rolemenu_done(
            self,
            interaction: discord.ComponentInteraction):
        """
        Pinged when the user is done setting up a role menu.
        """

        # Remove the buttons so they stop clicking stuff
        await interaction.response.edit_message(components=None)

        # Get and validate the embed
        message_embed = interaction.message.embeds[0]
        if not message_embed.fields:
            return await interaction.response.send_message(
                "You need to add some roles first!",
                ephemeral=True,
            )
        else:
            embed_roles: str = message_embed.fields[0].value  # pyright: ignore
        if not message_embed.description:
            return
        else:
            embed_content: str | None = message_embed.description  # pyright: ignore

        # Get the role IDs
        role_ids = [
            int(match.group(1))
            for match in re.finditer(
                r"<@&(\d+)>",
                embed_roles,
                re.MULTILINE,
            )
        ]

        # Make sure they gave some
        if not role_ids:
            return await interaction.edit_original_message(
                content="You need to add at least one role to the menu.",
                embeds=[],
            )

        # Get the actual roles
        guild = await self.bot.fetch_guild(interaction.guild_id)
        # roles do not need to be fetched individually since they're returned
        # in the guild payload
        roles = [
            role
            for role in guild.roles
            if role.id in role_ids
        ]

        # Make the dropdown
        dropdown = discord.ui.SelectMenu(
            custom_id="NEWROLEPICKER ROLE",
            options=[
                discord.ui.SelectOption(
                    label=role.name,
                    value=str(role.id),
                )
                for role in roles
            ]
        )

        # And send
        try:
            await interaction.channel.send(
                content=embed_content or "Pick a role!",
                components=discord.ui.MessageComponents(
                    discord.ui.ActionRow(dropdown),
                ),
            )
        except discord.HTTPException:
            await interaction.followup.send(
                content=embed_content or "Pick a role!",
                components=discord.ui.MessageComponents(
                    discord.ui.ActionRow(dropdown),
                ),
            )

    async def rolepicker_role(
            self,
            interaction: discord.ComponentInteraction,
            possible_role_id: str | None = None):
        """
        A user has pressed a button on an actual rolepicker.
        """

        # Get the role ID
        if possible_role_id:
            role_id = int(possible_role_id)
        else:
            role_id = int(interaction.data["values"][0].split(" ")[-1])

        # Get the role
        if interaction.guild is None:
            return
        elif isinstance(interaction.guild, discord.Guild):
            guild = interaction.guild
        else:
            guild = await self.bot.fetch_guild(interaction.guild.id)
        role = guild.get_role(role_id)
        if role is None:
            await interaction.response.send_message(
                "That role doesn't exist anymore :/",
                ephemeral=True,
            )

            # Remove the role from the dropdown
            try:
                await interaction.edit_original_message(
                    components=discord.ui.MessageComponents(
                        discord.ui.ActionRow(
                            discord.ui.SelectMenu(
                                custom_id="NEWROLEPICKER ROLE",
                                options=[
                                    option
                                    for option in (
                                        interaction
                                        .message
                                        .components[0]
                                        .components[0]
                                        .options
                                    )
                                    if int(option.value) != role_id
                                ],
                            ),
                        ),
                    ),
                )
            except discord.HTTPException:
                await interaction.edit_original_message(components=None)
            return

        # Add or remove the role
        user = cast(discord.Member, interaction.user)
        if role in user.roles:
            await user.remove_roles(role, reason="Role picker")
            await interaction.response.send_message(
                f"Removed the {role.mention} role.",
                components=discord.ui.MessageComponents.add_buttons_with_rows(
                    discord.ui.Button(
                        label="Re-add",
                        custom_id=f"NEWROLEPICKER ROLE {role.id}",
                    ),
                ),
                ephemeral=True,
            )
        else:
            await user.add_roles(role, reason="Role picker")
            await interaction.response.send_message(
                f"Gave you the {role.mention} role.",
                components=discord.ui.MessageComponents.add_buttons_with_rows(
                    discord.ui.Button(
                        label="Re-remove",
                        custom_id=f"NEWROLEPICKER ROLE {role.id}",
                    ),
                ),
                ephemeral=True,
            )


def setup(bot: vbu.Bot):
    x = RolePicker(bot)
    bot.add_cog(x)
