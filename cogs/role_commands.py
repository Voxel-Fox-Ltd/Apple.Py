import typing

import discord
from discord.ext import commands
import voxelbotutils as utils


class RoleCommands(utils.Cog):

    @utils.command()
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(send_messages=True)
    async def copyrolepermissions(self, ctx:utils.Context, copy_role:discord.Role, paste_role:discord.Role):
        """Copies the permissions from one role onto another"""

        try:
            await paste_role.edit(permissions=copy_role.permissions)
        except discord.HTTPException:
            return await ctx.send("Unable to edit role.")
        return await ctx.send("Edited.")

    @utils.command()
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(send_messages=True)
    async def permissions(self, ctx:utils.Context, user:discord.Member, channel:typing.Optional[discord.TextChannel]):
        """See all the permissions for a given user"""

        if channel is None:
            channel = ctx.channel
        channel_permissions = channel.permissions_for(user)
        guild_permissions = user.guild_permissions

        green_circle = '\U0001f7e2'
        red_circle = '\U0001f534'

        output = []
        for i in sorted(dir(channel_permissions)):
            cp = getattr(channel_permissions, i, None)
            gp = getattr(guild_permissions, i, None)
            if isinstance(cp, bool):
                permission_name = i.title().replace('Vc', 'VC').replace('Tts', 'TTS').replace('_', ' ')
                if i in ['connect', 'view_channel']:
                    continue
                if i in ['deafen_members', 'move_members', 'mute_members', 'priority_speaker', 'speak', 'stream', 'use_voice_activation']:
                    output.append(f"Guild({green_circle if gp else red_circle}) Channel(\U00002716) - **{permission_name}**")
                else:
                    output.append(f"Guild({green_circle if gp else red_circle}) Channel({green_circle if cp else red_circle}) - **{permission_name}**")
        await ctx.send('\n'.join(output))

    @utils.command()
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(send_messages=True)
    async def dumpmessage(self, ctx:utils.Context, message:discord.Message):
        """Dumps a message out into chat"""

        await ctx.send(f'```\n{message.content}\n```')

    @commands.command(cls=utils.Command)
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(send_messages=True)
    async def dumpmessagelist(self, ctx:utils.Context, message:discord.Message):
        """Dumps a message out into chat"""

        await ctx.send(f'```py\n{[i.encode("unicode_escape").decode() for i in list(message.content)]}\n```')


def setup(bot:utils.Bot):
    x = RoleCommands(bot)
    bot.add_cog(x)
