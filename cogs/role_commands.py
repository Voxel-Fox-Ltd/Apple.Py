import typing
import json

import discord
from discord.ext import commands
import voxelbotutils as utils


class RoleCommands(utils.Cog):

    @utils.command()
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(send_messages=True)
    async def copyrolepermissions(self, ctx:utils.Context, copy_role:discord.Role, paste_role:discord.Role):
        """
        Copies the permissions from one role onto another.
        """

        try:
            await paste_role.edit(permissions=copy_role.permissions)
        except discord.HTTPException:
            return await ctx.send("Unable to edit role.")
        return await ctx.send("Copied the permissions from {copy_role.mention} to {paste_role.mention}.", allowed_mentions=discord.AllowedMentions.none())

    @utils.command()
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(send_messages=True)
    async def permissions(self, ctx:utils.Context, user:typing.Union[discord.Member, discord.Role], channel:typing.Optional[discord.TextChannel]):
        """
        See all the permissions for a given user.
        """

        if channel is None:
            channel = ctx.channel
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

    @utils.command()
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(send_messages=True)
    async def dumpmessage(self, ctx:utils.Context, message:discord.Message):
        """
        Dumps a message out into chat.
        """

        await ctx.send(f'```\n{message.content}\n```')

    @utils.command(aliases=['dumpmessageembed'])
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(send_messages=True)
    async def dumpmessageembeds(self, ctx:utils.Context, message:discord.Message):
        """
        Dumps a message out into chat.
        """

        await ctx.send(f'```json\n{json.dumps([i.to_json() for i in message.embeds], indent=2)}\n```')

    @commands.command(cls=utils.Command)
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(send_messages=True)
    async def dumpmessagelist(self, ctx:utils.Context, message:discord.Message):
        """
        Dumps a message out into chat.
        """

        await ctx.send(f'```py\n{[i.encode("unicode_escape").decode() for i in list(message.content)]}\n```')


def setup(bot:utils.Bot):
    x = RoleCommands(bot)
    bot.add_cog(x)
