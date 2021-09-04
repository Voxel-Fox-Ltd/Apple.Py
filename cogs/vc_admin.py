import discord
from discord.ext import commands, vbu


class VCAdmin(vbu.Cog):

    @commands.group()
    async def vcadmin(self, ctx: vbu.Context):
        """
        The parent group for VC admin commands.
        """

        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @vcadmin.command(aliases=["set"])
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    @commands.guild_only()
    async def add(self, ctx: vbu.Context, channel: discord.VoiceChannel, role: discord.Role):
        """
        Sets a voice channel's admin role.
        """

        # Set the channel's admin role
        assert ctx.guild
        async with vbu.Database() as db:
            await db(
                """INSERT INTO vc_admins (guild_id, channel_id, role_id)
                VALUES ($1, $2, $3) ON CONFLICT (channel_id, role_id) DO UPDATE SET role_id = $3""",
                ctx.guild.id, channel.id, role.id
            )

        # Send a confirmation message
        await ctx.send(
            f"Set {channel.mention}'s admin role to {role.mention}",
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @vcadmin.command(aliases=["delete"])
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    @commands.guild_only()
    async def remove(self, ctx: vbu.Context, channel: discord.VoiceChannel):
        """
        Removes a voice channel's admin role.
        """

        # Remove the channel's admin role
        assert ctx.guild
        async with vbu.Database() as db:
            await db(
                """DELETE FROM vc_admins WHERE guild_id = $1 AND channel_id = $2""",
                ctx.guild.id, channel.id
            )

        # Send a confirmation message
        await ctx.send(
            f"Removed {channel.mention}'s admin role",
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @vcadmin.command()
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def role(self, ctx: vbu.Context, channel: discord.VoiceChannel):
        """
        Sends a voice channel's admin roles.
        """

        # Get the channel's admin roles
        assert ctx.guild
        async with vbu.Database() as db:
            roles_rows = await db(
                """SELECT role_id FROM vc_admins WHERE guild_id = $1 AND channel_id = $2""",
                ctx.guild.id, channel.id
            )

        # If there are no roles
        if not roles_rows:
            return await ctx.send(
                (
                    f"{channel.mention} does not have a VC administrator role set-up. Set one up by running the "
                    f"`{ctx.prefix}vcadmin add <channel_id> <role>` command."
                ),
            )

        # Get a the role object
        role = ctx.guild.get_role(roles_rows[0]['role_id'])

        # Make sure the role exists
        if not role:
            return await ctx.send(
                (
                    f"{channel.mention}'s VC administrator role is set to `{roles_rows[0]['role_id']}`, but "
                    f"that role does not exist. Please run the `{ctx.prefix}vcadmin add <role_id>` "
                    "command to reset the VC administrator role."
                ),
            )

        # Send the message
        await ctx.send(
            f"{channel.mention}'s VC administrator role is {role.mention}",
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @vbu.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """
        Give the user who's streaming the admin role
        """

        # Set up our variables
        guild = member.guild
        channel = after.channel

        # Make sure stream status updated and we're in a channel
        if before.self_stream == after.self_stream and before.channel == after.channel:
            self.logger.info(f"Ignoring voice state update for user {member.id} in channel {(after.channel or before.channel).id}")
            return

        # Get the database info
        async with vbu.Database() as db:
            roles_rows = await db(
                """SELECT * FROM vc_admins WHERE guild_id=$1 AND channel_id=$2""",
                guild.id, (channel or before.channel).id,
            )

        # Check that we're in a voice channel that we have a VC admin role for
        if not roles_rows:
            return

        # Get the role object
        role = guild.get_role(roles_rows[0]['role_id'])

        # Make sure the role exists
        if not role:
            self.logger.info(f"No role with ID {roles_rows[0]['role_id']}")
            return

        # Check that the user has either stopped streaming or begun streaming
        if (before.self_stream, before.channel) == (after.self_stream, after.channel):
            self.logger.info(f"No update in VC")
            return

        # Determine the method we'll use
        method = {
            True: member.add_roles,
            False: member.remove_roles,
        }[after.channel and after.self_stream]

        # Apply the method
        await method(role, reason="Streaming status changed.")

        # Log our info
        self.logger.info(f"Gave {member.id} the role {role.id} for channel {channel.id} for stream status change.")


def setup(bot: vbu.Bot):
    x = VCAdmin(bot)
    bot.add_cog(x)
