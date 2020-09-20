import discord

from cogs import utils


class LiveVCPermissionHandler(utils.Cog):

    LIVE_VC_CHANNEL_ID = 732212297958817822

    PERMISSION_TIERS = {
        -1: None,  # Everyone role
        -2: 653008615912898570,  # Cerberus 1
        -3: 674748125755211803,  # Cerberus 2
        -4: 676516378295009288,  # Cerberus 3
        -5: 679145985653342228,  # Cerberus 4
        -6: 680881546051584066,  # Cerberus 5
        -7: 690161286251675826,  # Cerberus 6
        -8: 726234884997251162,  # Cerberus 7
        -9: 744128973608452106,  # Cerberus 8
    }

    @utils.Cog.listener()
    async def on_guild_channel_update(self, before:discord.TextChannel, after:discord.TextChannel):
        """Update permissions for the live VC based on the name dab"""

        # Check the channel
        if after.id != self.LIVE_VC_CHANNEL_ID:
            return

        # See if its name changed
        if before.name == after.name:
            return

        # Sick let's update the permissions
        permissions = after.overwrites.copy()
        for tick, role_id in self.PERMISSION_TIERS.items():
            if role_id is None:
                role = after.guild.default_role
            else:
                role = after.guild.get_role(role_id)
            permissions[role] = after.overwrites.get(role, discord.PermissionOverwrite())
            permissions[role].update(connect=after.name.split(' ')[0][tick] == '1' or None)
            if role_id is None:
                permissions[role].update(connect=None if after.name.split(' ')[0][tick] == '1' else False)

        # And update the channel
        await after.edit(overwrites=permissions)


def setup(bot:utils.Bot):
    x = LiveVCPermissionHandler(bot)
    bot.add_cog(x)
