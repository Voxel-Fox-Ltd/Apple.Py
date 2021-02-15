import io

import discord
from discord.ext import commands
import voxelbotutils as utils


class AnalyticsCommands(utils.Cog):
    """
    Get all links ever sent in a channel and dump them to a txt file.

    Takes a channel as an argument or defaults to the channel in which the command was invoked.
    """
    @utils.command()
    @utils.cooldown.cooldown(1, 600, commands.BucketType.guild)
    @commands.bot_has_permissions(read_message_history=True, send_messages=True, attach_file=True)
    def linkdump(self, ctx:utils.Context, target_channel:discord.TextChannel=None):
        if target_channel is None:
            target_channel = ctx.channel

        await ctx.send('Processing...')
        all_links = []
        for message in target_channel.history():
            for embed in message.embeds:
                all_links.append(embed.url)

        file_stream = io.StringIO('\n'.join(all_links))
        discord_file = discord.File(file_stream, filename='links.txt')
        await ctx.send(f'Here are all the links ever sent in the {target_channel.name} channel:', file=discord_file)


def setup(bot:utils.Bot):
    x = AnalyticsCommands(bot)
    bot.add_cog(x)