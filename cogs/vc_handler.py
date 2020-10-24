import discord
import voxelbotutils as utils


class VCHandler(utils.Cog):

    async def cache_setup(self, db):
        data = await self.bot._get_list_table_data(db, "channel_list", "MaxVCMembers")
        for row in data:
            self.bot.guild_settings[row['guild_id']].setdefault('max_vc_members', dict())[row['channel_id']] = int(row['value'])

    @utils.Cog.listener()
    async def on_voice_state_update(self, member:discord.Member, before:discord.VoiceState, after:discord.VoiceState):
        """Pinged when a user joins/leaves a voice chat"""

        # Check how many people are in the VC
        channels = list(set([i for i in [after.channel, before.channel] if i is not None]))
        for channel in channels:

            # Get allowed data
            allowed_members_for_channel = self.bot.guild_settings[member.guild.id].setdefault('max_vc_members', dict()).get(channel.id)
            if allowed_members_for_channel is None:
                continue

            # Set up some lambdas
            user_is_muted = lambda vs: any([vs.deaf, vs.mute, vs.self_mute, vs.self_deaf])
            user_is_streaming = lambda vs: any([vs.self_stream, vs.self_video])
            user_counts_as_muted = lambda vs: user_is_muted(vs) and not user_is_streaming(vs)

            # See how many are muted
            current_muted_member_count = len([i for i in channel.members if user_counts_as_muted(i.voice)])

            # # See if we need to add our newly-cached member to that
            # if after.channel == channel:
            # TODO

            new_limit = allowed_members_for_channel + current_muted_member_count
            try:
                await channel.edit(user_limit=new_limit)
                self.logger.info(f"Updated user limit for channel {channel.id} to {new_limit}")
            except discord.Forbidden as e:
                self.logger.error(f"Failed to update user limit for channel {channel.id} - {e}")


def setup(bot:utils.Bot):
    x = VCHandler(bot)
    bot.add_cog(x)
