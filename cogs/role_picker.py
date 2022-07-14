from typing import Optional, Union, List
from uuid import uuid4

import discord
from discord.ext import commands, vbu


class RolePicker(vbu.Cog[vbu.Bot]):

    @commands.group(
        application_command_meta=commands.ApplicationCommandMeta(
            guild_only=True,
            permissions=discord.Permissions(manage_roles=True, manage_guild=True),
        ),
    )
    @commands.is_slash_command()
    async def rolepicker(self, _: vbu.SlashContext):
        pass

    @rolepicker.command(
        name="create",
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="name",
                    type=discord.ApplicationCommandOptionType.string,
                    description="The name of your role picker. Only you can see this.",
                ),
                discord.ApplicationCommandOption(
                    name="text",
                    type=discord.ApplicationCommandOptionType.string,
                    description="The text you want to be displayed above the dropdown.",
                ),
                discord.ApplicationCommandOption(
                    name="channel",
                    type=discord.ApplicationCommandOptionType.channel,
                    description="The place you want to create the role picker.",
                    channel_types=[discord.ChannelType.text],
                    required=False,
                ),
                discord.ApplicationCommandOption(
                    name="min_roles",
                    type=discord.ApplicationCommandOptionType.integer,
                    description="The minimum number of roles that the user can have.",
                    min_value=0,
                    required=False,
                ),
                discord.ApplicationCommandOption(
                    name="max_roles",
                    type=discord.ApplicationCommandOptionType.integer,
                    description="The maximum number of roles that the user can have.",
                    max_value=25,
                    required=False,
                ),
            ],
            guild_only=True,
            permissions=discord.Permissions(manage_roles=True, manage_guild=True),
        ),
    )
    @commands.is_slash_command()
    async def rolepicker_create(
            self, 
            ctx: vbu.SlashContext,
            name: str,
            text: str,
            channel: Optional[discord.TextChannel] = None,
            min_roles: Optional[int] = None,
            max_roles: Optional[int] = None):
        """
        Create a new role picker message.
        """

        # Make sure the things they gave are valid
        if min_roles and max_roles and max_roles < min_roles:
            return await ctx.interaction.response.send_message(
                "The maximum cannot be a higher number than the minimum.",
                ephemeral=True,
            )

        # Only work if they can send messages in that channel
        channel = channel or ctx.channel  # type: ignore - will be a TextChannel, I guess
        assert channel
        author: discord.Member = ctx.author  # type: ignore - will be a member
        assert author
        if not channel.permissions_for(author).send_messages:
            return await ctx.interaction.response.send_message(
                "You cannot send messages into that channel.",
                ephemeral=True,
            )

        # Send message
        await ctx.interaction.response.defer(ephemeral=True)
        component_id = uuid4()
        message = await channel.send(
            text,
            components=discord.ui.MessageComponents(
                discord.ui.ActionRow(
                    discord.ui.SelectMenu(
                        custom_id=f"ROLEPICKER {component_id}",
                        options=[
                            discord.ui.SelectOption(
                                label="No roles have been added :(",
                                value="NULL",
                            ),
                        ],
                    ),
                ),
            ),
        )

        # Send and store
        async with vbu.Database() as db:
            await db.call(
                """
                INSERT INTO
                    role_pickers
                    (
                        guild_id,
                        name,
                        message_id,
                        channel_id,
                        component_id,
                        min_roles,
                        max_roles
                    )
                VALUES
                    (
                        $1,  -- guild_id
                        $2,  -- name
                        $3,  -- message_id
                        $4,  -- channel_id
                        $5,  -- component_id
                        $6,  -- min_roles
                        $7  -- max_role
                    )
                """,
                ctx.guild.id, name, message.id,
                message.channel.id, component_id,
                min_roles, max_roles,
            )

        # And tell them about it
        await ctx.interaction.followup.send(
            "Created role picker!~",
            ephemeral=True,
        )

    @rolepicker.command(
        name="add",
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="name",
                    type=discord.ApplicationCommandOptionType.string,
                    description="The name of the role picker that you want to modify.",
                    autocomplete=True,
                ),
                discord.ApplicationCommandOption(
                    name="role",
                    type=discord.ApplicationCommandOptionType.role,
                    description="The role you want to add to the role picker.",
                ),
            ],
            guild_only=True,
            permissions=discord.Permissions(manage_roles=True, manage_guild=True),
        ),
    )
    @commands.is_slash_command()
    async def rolepicker_add(
            self,
            ctx: vbu.SlashContext,
            name: str,
            role: discord.Role):
        """
        Add a new role to a role picker.
        """

        # Defer so we can fetch
        await ctx.interaction.response.defer(ephemeral=True)

        # Fetch some values from the API
        author: discord.Member
        author = ctx.guild.fetch_member(ctx.author.id)  # type: ignore - author will definitely exist
        guild: discord.Guild = ctx.guild
        guild_roles = guild.roles

        # Make sure the role they gave is lower than their top
        author_top_role = [i for i in guild_roles if i.id == author.roles[-1].id][0]
        role = [i for i in guild_roles if i.id == role.id][0]
        if author_top_role < role:
            return await ctx.interaction.followup.send(
                "Your top role is below the one you're trying to manage.",
                ephemeral=True,
            )

        # Add that role to the database
        async with vbu.Database() as db:
            await db.call(
                """
                INSERT INTO
                    role_picker_role
                    (
                        guild_id,
                        name,
                        role_id
                    )
                VALUES
                    (
                        $1,  -- guild_id
                        $2,  -- name
                        $3  -- role_id
                    )
                """,
                guild.id, name, role.id,
            )

        # Tell the user it's done
        await ctx.interaction.followup.send(
            "Added role to role picker!~",
            ephemeral=True,
        )
        self.bot.dispatch("role_picker_update", guild, name)

    @rolepicker.command(
        name="remove",
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="name",
                    type=discord.ApplicationCommandOptionType.string,
                    description="The name of the role picker that you want to modify.",
                    autocomplete=True,
                ),
                discord.ApplicationCommandOption(
                    name="role",
                    type=discord.ApplicationCommandOptionType.string,
                    description="The role you want to remove from the role picker.",
                ),
            ],
            guild_only=True,
            permissions=discord.Permissions(manage_roles=True, manage_guild=True),
        ),
    )
    @commands.is_slash_command()
    async def rolepicker_remove(
            self,
            ctx: vbu.SlashContext,
            role: discord.Role):
        """
        Remove a role from one of your role pickers.
        """

        ...

    @vbu.Cog.listener()
    async def on_role_picker_update(
            self,
            guild: Union[discord.abc.Snowflake, discord.Guild],
            role_picker_name_or_component_id: str):
        """
        Update one of the published role pickers.
        """

        # Get the current data
        async with vbu.Database() as db:
            role_rows = await db.call(
                """
                SELECT
                    role_pickers.message_id,
                    role_pickers.channel_id,
                    role_pickers.component_id,
                    role_pickers.min_roles,
                    role_pickers.max_roles,
                    role_picker_role.role_id
                FROM
                    role_picker_role
                LEFT JOIN
                    role_pickers
                ON
                    role_picker_role.guild_id = role_pickers.guild_id
                AND
                    role_picker_role.name = role_pickers.name
                WHERE
                    guild_id = $1
                AND
                    (
                        role_picker_role.name = $2
                        OR
                        role_picker_role.component_id = $2
                    )
                """,
                guild.id, role_picker_name_or_component_id,
            )
            if not role_rows:
                role_rows = await db.call(
                    """
                    SELECT
                        message_id,
                        channel_id,
                        component_id,
                        min_roles,
                        max_roles
                    FROM
                        role_pickers
                    WHERE
                        guild_id = $1
                    AND
                        (
                            name = $2
                            OR
                            component_id = $2
                        )
                    """,
                    guild.id, role_picker_name_or_component_id,
                )

        # Get a partial message we can edit
        messageable = self.bot.get_partial_messageable(role_rows[0]['channel_id'])
        message = messageable.get_partial_message(role_rows[0]['message_id'])

        # Get the roles
        guild_roles: List[discord.Role]
        if isinstance(guild, discord.Guild):
            guild_roles = await guild.fetch_roles()
        else:
            guild = await self.bot.fetch_guild(guild.id)
            guild_roles = guild.roles

        # Create the menu options
        menu_options: List[discord.ui.SelectOption] = [
            discord.ui.SelectOption(
                label="No roles have been added :(",
                value="NULL",
            ),
        ]
        if "role_id" in role_rows[0]:
            menu_options = [
                discord.ui.SelectOption(
                    label=role.name,
                    value=i['role_id'],
                )
                for i in role_rows
                if (role := discord.utils.get(guild_roles, id=i['role_id']))
            ]

        # Edit the message
        row = role_rows[0]
        await message.edit(
            components=discord.ui.MessageComponents(
                discord.ui.ActionRow(
                    discord.ui.SelectMenu(
                        custom_id=f"ROLEPICKER {row['component_id']}",
                        options=menu_options[:25],
                        min_values=row['min_roles'],
                        max_values=row['max_roles'],
                    ),
                ),
            ),
        )

    @vbu.Cog.listener()
    async def on_component_interaction(
            self,
            interaction: discord.Interaction[str]):
        """
        Listen for a rolepicker component being clicked and manage
        that for the user.
        """

        # Make sure it's a rolepicker component
        if not interaction.custom_id.startswith("ROLEPICKER"):
            return
        await interaction.response.defer(ephemeral=True)
        component_id = interaction.custom_id.split(" ")[1]
        if component_id == "NULL":
            return await interaction.response.defer()

        # See what they selected
        picked_role_ids = [int(i) for i in interaction.values]  # type: ignore - interaction values won't be none here
        guild_id: int = interaction.guild_id  # type: ignore - this will be run in a guild
        guild: discord.Guild = interaction.guild or await self.bot.fetch_guild(guild_id)
        picked_roles = [i for i in guild.roles if i.id in picked_role_ids]

        # See if they have any of those roles currently
        user: discord.Member = interaction.user  # type: ignore - user is definitely a member object
        user_roles: List[discord.Role] = user.roles
        roles_they_have_currently = [i for i in user_roles for i in picked_roles]

        # See if they have ALL of the roles they picked
        if len(roles_they_have_currently) == len(picked_roles):
            try:
                await user.remove_roles(*picked_roles, reason="Role picker")
            # except discord.NotFound:
            #     await interaction.followup.send(
            #         "I can't find one of the roles you picked in the server any more.",
            #         ephemeral=True,
            #     )
            #     self.bot.dispatch("role_picker_update", guild, component_id)
            #     return
            except discord.Forbidden:
                await interaction.followup.send(
                    "I'm unable to remove that role from you.",
                    ephemeral=True,
                )
                return
            await interaction.followup.send(
                vbu.format("Removed {0} {0:plural,role,roles} from you.", len(picked_roles)),
                ephemeral=True,
            )
            return

        # If not then we'll just add them to the user
        try:
            await user.add_roles(*picked_roles, reason="Role picker")
        except discord.NotFound:
            await interaction.followup.send(
                "I can't find one of the roles you picked in the server any more.",
                ephemeral=True,
            )
            self.bot.dispatch("role_picker_update", guild, component_id)
            return
        except discord.Forbidden:
            await interaction.followup.send(
                "I'm unable to add that role to you.",
                ephemeral=True,
            )
            return
        await interaction.followup.send(
            vbu.format("Added {0} {0:plural,role,roles} to you.", len(picked_roles)),
            ephemeral=True,
        )
        return


def setup(bot: vbu.Bot):
    x = RolePicker(bot)
    bot.add_cog(x)
