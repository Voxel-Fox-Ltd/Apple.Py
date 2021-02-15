import io
import re
import csv

import discord
from discord.ext import commands
import voxelbotutils as utils


DISCORD_EMOTE_REGEX = re.compile(r'<:(\w*):\d*>')


class AnalyticsCommands(utils.Cog):
    # todo: add progress printouts
    @utils.command()
    @utils.cooldown.cooldown(1, 6000, commands.BucketType.guild)
    @commands.bot_has_permissions(read_message_history=True, send_messages=True, attach_files=True)
    def linkdump(self, ctx:utils.Context, target_channels:commands.Greedy[discord.TextChannel]=None, regex=None):
        """
        Get all links ever sent in a channel and dump them to a txt file.

        Takes channels as arguments, or defaults to the channel in which the command was invoked.
        """
        if target_channels is None:
            target_channels = [ctx.channel]
        if regex is not None:
            try:
                regex = re.compile(regex)
            except re.error:
                return await ctx.send('Bad regex.')

        await ctx.send('Processing...')
        all_links = []
        for target_channel in target_channels:
            for message in target_channel.history(limit=None):
                for embed in message.embeds:
                    if regex is not None:
                        if re.fullmatch(regex, embed.url):
                            all_links.append(embed.url)
                    else:
                        all_links.append(embed.url)

        with io.StringIO('\n'.join(all_links)) as file_stream:
            discord_file = discord.File(file_stream, filename='links.txt')
            return await ctx.send(f'Here are all the links ever sent in the channels:',
                                  file=discord_file)

    @utils.command(name='analyse-emote-usage')
    @utils.cooldown.cooldown(1, 6000, commands.BucketType.guild)
    @commands.bot_has_permissions(read_message_history=True, send_messages=True, attach_files=True)
    def emotes(self, ctx:utils.Context, target_channels:commands.Greedy[discord.TextChannel]=None):
        """
        Get a csv containing the timestamp of every discord emote ever sent in a guild.

        Takes channels as arguments, or defaults to every channel in the guild.
        The user can take this and make a graph or whatever. Useful for figuring out which emotes to remove
        when you're at the cap!
        """
        if target_channels is None:
            target_channels = ctx.guild.channels

        await ctx.send('Processing...')

        with io.StringIO as file_stream:
            csvw = csv.writer(file_stream)
            for channel in target_channels:
                if channel.type == discord.ChannelType.text:
                    for message in channel.history(limit=None):
                        emotes_used = re.findall(DISCORD_EMOTE_REGEX, message.content)
                        message_timestamp = message.created_at.timestamp()
                        csvw.writerows([[message_timestamp, emote_used] for emote_used in emotes_used])

            discord_file = discord.File(file_stream, filename='emotes.csv')
            return await ctx.send('Here are all the emotes used in this guild (server):', file=discord_file)


def setup(bot:utils.Bot):
    x = AnalyticsCommands(bot)
    bot.add_cog(x)