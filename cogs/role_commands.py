import typing
import json

import discord
from discord.ext import commands, vbu


class RoleCommands(vbu.Cog):

    @commands.command(add_slash_command=False)
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(send_messages=True)
    @commands.guild_only()
    async def permissions(self, ctx: vbu.Context, user: typing.Union[discord.Member, discord.Role], channel: typing.Optional[discord.TextChannel] = None):
        """
        See all the permissions for a given user.
        """

        if channel is None:
            channel = ctx.channel
        assert isinstance(channel, discord.TextChannel)
        channel_permissions = channel.overwrites_for(user)
        if isinstance(user, discord.Role):
            guild_permissions = user.permissions
        else:
            guild_permissions = user.guild_permissions

        # Set up some perms baybeee
        green_circle = '\U0001f7e2'
        red_circle = '\U0001f534'
        cross_emoji = '\U00002716'
        base_permissions = discord.Permissions(2080831743)

        output = [f"**Permissions for {user.mention}**" if channel == ctx.channel else f"**Permissions for {user.mention} in {channel.mention}**"]
        for permission_api_name, o in base_permissions:
            if o is False:
                continue
            has_guild_permission = getattr(guild_permissions, permission_api_name, None)
            has_channel_permission = getattr(channel_permissions, permission_api_name, None)

            # if isinstance(cp, bool):
            permission_name = permission_api_name.title().replace('Vc', 'VC').replace('Tts', 'TTS').replace('_', ' ')
            if permission_api_name in ['connect', 'view_channel']:
                continue
            else:
                output.append(f"Guild({green_circle if has_guild_permission else red_circle}) Channel({green_circle if has_channel_permission is True else red_circle if has_channel_permission is False else cross_emoji}) - **{permission_name}**")
        await ctx.send('\n'.join(output), allowed_mentions=discord.AllowedMentions(users=False, roles=False, everyone=False))


def setup(bot: vbu.Bot):
    x = RoleCommands(bot)
    bot.add_cog(x)
