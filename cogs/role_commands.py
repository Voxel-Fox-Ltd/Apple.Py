import typing

import discord
from discord.ext import commands

from cogs import utils


class RoleCommands(utils.Cog):

    @commands.command(cls=utils.Command)
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(send_messages=True)
    async def copyrolepermissions(self, ctx:utils.Context, copy_role:discord.Role, paste_role:discord.Role):
        """Copies the permissions from one role onto another"""

        try:
            await paste_role.edit(permissions=copy_role.permissions)
        except discord.HTTPException:
            return await ctx.send("Unable to edit role.")
        return await ctx.send("Edited.")

    @commands.command(cls=utils.Command)
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(send_messages=True)
    async def permissions(self, ctx:utils.Context, user:discord.Member, channel:typing.Optional[discord.TextChannel]):
        """See all the permissions for a given user"""

        if channel is None:
            channel = ctx.channel
        permissions = channel.permissions_for(user)

        output = []
        for i in dir(permissions):
            v = getattr(permissions, i, None)
            if isinstance(v, bool):
                output.append(f"{i} - {str(v).lower()}")
        await ctx.send('\n'.join(output))

    @commands.command(cls=utils.Command)
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
