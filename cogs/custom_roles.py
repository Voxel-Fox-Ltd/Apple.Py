from typing import cast, TYPE_CHECKING

import discord
from discord.ext import commands, vbu

from .types.bot import Bot


class CustomRolesCog(vbu.Cog[Bot]):

    ROLE_NAME_PREFIX = "(Custom) "

    # Wether custom role requirement checks should be ignored when the required
    # role is set to a deleted role.
    INVALIDATE_DELETED_REQUIRED_ROLE = False

    async def _check_custom_role_requirements(
            self,
            ctx: vbu.SlashContext[discord.Guild]) -> bool:
        """
        A method that checks if a user is allowed to use custom roles.
        This method responds to the interaction, and thus should only be
        used on a :class:`SlashContext` that hasn't been responded to yet.
        Returns True when successful and when the interaction hasn't been
        responded to yet.
        """

        required_role_id = self.bot.guild_settings[ctx.guild.id][
            "custom_role_requirement_role_id"
        ]

        # no requirements, no problems
        if required_role_id is None:
            return True

        # required role doesn't exist?
        if required_role_id not in ctx.guild._roles:
            if self.INVALIDATE_DELETED_REQUIRED_ROLE:
                await ctx.interaction.response.send_message(
                    (
                        "This server has it's required role for custom roles "
                        "set to a deleted role."
                    ),
                    ephemeral=True,
                    allowed_mentions=discord.AllowedMentions.none(),
                )
                return False
            return True

        # dont have the required role?
        if required_role_id not in ctx.author.role_ids:
            mention = ctx.get_mentionable_role(required_role_id).mention
            await ctx.interaction.response.send_message(
                f"You need the {mention} role to use this command.",
                ephemeral=True,
                allowed_mentions=discord.AllowedMentions.none(),
            )
            return False

        return True

    async def _update_custom_role_property(
            self,
            ctx: vbu.SlashContext[discord.Guild],
            **properties):
        """
        A method that updates the properties of the custom role of the
        `ctx.author`. This method responds to the interaction, and thus
        should only be used on a :class:`SlashContext` that hasn't been
        responded to yet. Returns True when successful and when the
        interaction hasn't been responded to yet.
        """

        # nothing to change ¯\_(ツ)_/¯
        if not properties:
            return

        async with vbu.Database() as db:
            rows = await db.call(
                """
                SELECT
                    role_id
                FROM
                    custom_roles
                WHERE
                    guild_id = $1
                    AND user_id = $2
                """,
                ctx.guild.id,
                ctx.author.id,
            )

            # no custom role?
            if not rows or not rows[0]:
                await ctx.interaction.response.send_message(
                    "You don't have a custom role!",
                    ephemeral=True,
                    allowed_mentions=discord.AllowedMentions.none(),
                )
                return

            custom_role = ctx.guild.get_role(rows[0]["role_id"])

            # invalid custom role ID, or outdated role cache?
            if custom_role is None:
                await ctx.interaction.followup.send(
                    (
                        "I couldn't locate your saved custom role in this "
                        "server. Please create a new role."
                    ),
                    ephemeral=True,
                    allowed_mentions=discord.AllowedMentions.none(),
                )
                await db.call(
                    """
                    DELETE FROM
                        custom_roles
                    WHERE
                        guild_id = $1
                        AND user_id = $2
                    """,
                    ctx.guild.id,
                    ctx.author.id,
                )
                return

        # defer cuz this part can take anywhere from 1 to 10 seconds
        await ctx.defer()
        await custom_role.edit(**properties)

        # fancy string interpolation :>
        if len(properties) <= 2:
            text = ", and ".join(f"{k} to {v}" for k, v in properties.items())
            await ctx.interaction.followup.send(f"Changed your custom role's {text}.")
        else:
            last_key, last_value = properties.popitem()
            text = ", ".join(f"{k} to {v}" for k, v in properties.items())
            await ctx.interaction.followup.send(
                f"Changed your custom role's {text}, and {last_key} to {last_value}.",
                allowed_mentions=discord.AllowedMentions.none(),
            )

    @vbu.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """
        Handles the deletion of custom roles when members leave servers.
        """

        if TYPE_CHECKING:
            member.guild = cast(discord.Guild, member.guild)

        async with vbu.Database() as db:
            rows = await db.call(
                """
                SELECT
                    role_id
                FROM
                    custom_roles
                WHERE
                    guild_id = $1
                    AND user_id = $2
                """,
                member.guild.id,
                member.id,
            )

            # no custom role?
            if not rows:
                return

            custom_role: discord.Role | None
            custom_role = member.guild.get_role(rows[0]["role_id"])

            # no role to delete if we cant even find it
            if custom_role is None:
                return

            await custom_role.delete(
                reason=f"Custom role owner {str(member)!r} left the server."
            )
            await db.call(
                """
                DELETE FROM
                    custom_roles
                WHERE
                    guild_id = $1
                    AND user_id = $2
                """,
                member.guild.id,
                member.id,
            )

    @vbu.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """
        Handles custom role-related processes when a member gets updated.
        """

        if TYPE_CHECKING:
            before.guild = cast(discord.Guild, before.guild)
            after.guild = cast(discord.Guild, after.guild)

        async with vbu.Database() as db:
            rows = await db.call(
                """
                SELECT
                    role_id
                FROM
                    custom_roles
                WHERE
                    guild_id = $1
                    AND user_id = $2
                """,
                after.guild.id,
                after.id,
            )

            # no custom role?
            if not rows:
                return

            # does the role exist?
            custom_role = after.guild.get_role(rows[0]["role_id"])
            if custom_role is None:
                return

            # does the user not have the role, or have it for valid reasons?
            required_role_id = self.bot.guild_settings[after.guild.id][
                "custom_role_requirement_role_id"
            ]
            if custom_role in after.roles and (
                required_role_id is None or required_role_id in after.role_ids
            ):
                return

            # delete the user's role cuz it was removed from their role list
            try:
                await custom_role.delete(
                    reason=f"Custom role was removed from {str(after)!r}'s profile."
                )

            # role was prolly deleted instead of removed
            except discord.HTTPException:
                pass

            await db.call(
                """
                DELETE FROM
                    custom_roles
                WHERE
                    guild_id = $1
                    AND user_id = $2
                """,
                after.guild.id,
                after.id,
            )

    @vbu.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        """
        Alters changes that have been done manually to custom roles, like
        manual repositioning or manual renaming.
        """

        async with vbu.Database() as db:
            rows = await db.call(
                """
                SELECT
                *
                FROM
                    custom_roles
                WHERE
                    guild_id = $1
                    AND role_id = $2
                """,
                after.guild.id,
                after.id,
            )

        # no custom rolz no problms
        if not rows:
            return

        updated_properties = {}

        # manual name change? better make sure they followed the custom
        # role naming convention
        if before.name != after.name:
            if not after.name.startswith(self.ROLE_NAME_PREFIX):
                updated_properties["name"] = self.ROLE_NAME_PREFIX + after.name

        parent_role = after.guild.get_role(
            self.bot.guild_settings[after.guild.id]["custom_role_parent_role_id"]
        )

        # make sure the custom role position is OK if a parent role is supplied
        if parent_role is not None:
            if before.position != after.position and after.position != max(
                1, parent_role.position - 1
            ):  # pos 0 = illegal
                updated_properties["position"] = max(1, parent_role.position - 1)

        if updated_properties:
            await after.edit(
                **updated_properties,
                reason=(
                    "Applied prefix to custom role name and/or repositioned "
                    "custom role."
                ),
            )

    @vbu.Cog.listener()
    async def on_custom_role_requirement_update(self, required_role: discord.Role):
        """
        Handlers the removal of custom roles when the requirements get updated.
        """

        # for some reason ctx.guild.members is empty, but getting it
        # again via bot bot.get_guild fixes it? WeirdChamp
        guild: discord.Guild = self.bot.get_guild(required_role.guild.id)

        async with vbu.Database() as db:
            rows = await db.call(
                """
                SELECT
                    user_id, role_id
                FROM
                    custom_roles
                WHERE
                    guild_id = $1
                """,
                guild.id,
            )

            for row in rows:
                member = guild.get_member(row["user_id"])

                # couldn't find member, they prolly left while the bot was off
                if member is None:
                    continue

                custom_role = guild.get_role(rows[0]["role_id"])

                # custom role aint even there
                if custom_role is None:
                    continue

                # member still meets the requirements
                if required_role in member.roles:
                    continue

                # remove role cuz member doesnt meet requirements
                await custom_role.delete(
                    reason=f"C{str(member)!r} no longer meets the requirements for owning a custom role."
                )
                await db.call(
                    """
                    DELETE FROM
                        custom_roles
                    WHERE
                        guild_id = $1
                        AND user_id = $2
                    """,
                    guild.id,
                    member.id,
                )

    @vbu.Cog.listener()
    async def on_custom_role_parent_update(self, parent_role: discord.Role):
        """
        Handles the repositioning of custom roles when their parent role
        gets updated.
        """

        async with vbu.Database() as db:
            rows = await db(
                """
                SELECT
                    role_id
                FROM
                    custom_roles
                WHERE
                    guild_id = $1
                """,
                parent_role.guild.id,
            )
            for row in rows:
                custom_role = parent_role.guild.get_role(row["role_id"])

                # custom role aint even there
                if custom_role is None:
                    continue

                # switchin positions 😩
                await custom_role.edit(
                    position=max(1, parent_role.position - 1),  # pos 0 = illegal
                    reason="Custom role's parent position was updated.",
                )

    @commands.group(
        "customrole", application_command_meta=commands.ApplicationCommandMeta()
    )
    @commands.is_slash_command()
    async def custom_role(self, _):
        ...

    @custom_role.command(
        "create", application_command_meta=commands.ApplicationCommandMeta()
    )
    @commands.bot_has_permissions(manage_roles=True)
    @commands.guild_only()
    @commands.is_slash_command()
    async def custom_role_create(self, ctx: vbu.SlashContext):
        """
        Creates a custom role.
        """

        if TYPE_CHECKING:
            # we can safely assume theres a guild
            ctx.guild: discord.Guild = cast(discord.Guild, ctx.guild)

        if not await self._check_custom_role_requirements(ctx):
            return

        async with vbu.Database() as db:
            rows = await db.call(
                """
                SELECT
                    *
                FROM
                    custom_roles
                WHERE
                    guild_id = $1
                    AND user_id = $2
                """,
                ctx.guild.id,
                ctx.author.id,
            )

            if rows:
                await ctx.interaction.response.send_message(
                    "You've already created a custom role.",
                    ephemeral=True,
                    allowed_mentions=discord.AllowedMentions.none(),
                )
                return

            await ctx.defer()

            custom_role = await ctx.guild.create_role(
                reason=f"Custom role, requested by {str(ctx.author)!r}.",
                permissions=discord.Permissions.none(),
            )
            await db(
                """INSERT INTO custom_roles VALUES ($1, $2, $3)""",
                ctx.guild.id,
                ctx.author.id,
                custom_role.id,
            )

            parent_role = ctx.guild.get_role(
                self.bot.guild_settings[ctx.guild.id]["custom_role_parent_role_id"]
            )

            if parent_role is None:
                position = 1
            else:
                position = max(1, parent_role.position - 1)  # pos 0 = illegal

            try:
                await custom_role.edit(
                    name=f"{self.ROLE_NAME_PREFIX}{ctx.author.name}'s role",
                    position=position,
                )
            except discord.HTTPException:
                await custom_role.delete()
                await db(
                    "DELETE FROM custom_roles WHERE guild_id=$1 AND user_id=$2",
                    ctx.guild.id,
                    ctx.author.id,
                )
                raise
            await ctx.author.add_roles(custom_role)

        await ctx.interaction.followup.send(
            "Created your custom role!",
            ephemeral=False,
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @custom_role.command(
        "colour",
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="colour",
                    description="Your new role colour, (eg, red, #49E78F, rgb(235, 78, 59)).",
                    type=discord.ApplicationCommandOptionType.string,
                )
            ]
        ),
    )
    @commands.bot_has_permissions(manage_roles=True)
    @commands.guild_only()
    @commands.is_slash_command()
    async def custom_role_colour(
        self, ctx: vbu.SlashContext, colour: vbu.converters.ColourConverter
    ):
        """
        Changes the colour of your custom role.
        """

        if not await self._check_custom_role_requirements(ctx):
            return
        await self._update_custom_role_property(ctx, colour=colour)

    @custom_role.command(
        "name",
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="name",
                    description="Your new custom role name.",
                    type=discord.ApplicationCommandOptionType.string,
                )
            ]
        ),
    )
    @commands.bot_has_permissions(manage_roles=True)
    @commands.guild_only()
    @commands.is_slash_command()
    async def custom_role_name(self, ctx: vbu.SlashContext, name: str):
        """
        Changes the name of your custom role.
        """

        if not await self._check_custom_role_requirements(ctx):
            return
        await self._update_custom_role_property(
            ctx, name=f"{self.ROLE_NAME_PREFIX}{name}"
        )

    @custom_role.command(
        "emoji",
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="emoji",
                    description="Your new role emoji.",
                    type=discord.ApplicationCommandOptionType.string,
                )
            ]
        ),
    )
    @commands.bot_has_permissions(manage_roles=True)
    @commands.guild_only()
    @commands.is_slash_command()
    async def custom_role_emoji(
        self, ctx: vbu.SlashContext, emoji: commands.EmojiConverter | str
    ):
        """
        Changes the emoji of your custom role.
        """

        if not await self._check_custom_role_requirements(ctx):
            return

        # need lvl 2 / 7 boosts for emoji icons
        if ctx.guild.premium_subscription_count < 7:
            await ctx.interaction.response.send_message(
                "This command requires a level 2 server.", ephemeral=True
            )
            return

        await self._update_custom_role_property(ctx, icon=emoji)


def setup(bot: vbu.Bot):
    x = CustomRolesCog(bot)
    bot.add_cog(x)
