import typing
from datetime import datetime as dt, timedelta
import json
from base64 import b64encode
import io

import discord
import voxelbotutils as vbu

from cogs import utils


class PhoenixWrightCommands(vbu.Cog):

    @vbu.command(enabled=False)
    async def phoenix(self, ctx: vbu.Context, after: discord.Message, before: typing.Optional[discord.Message], *characters: str):
        """
        Makes you an Objection.lol file for you to use as a base.
        """

        # Sort out our timestamps
        after = after.created_at - timedelta(seconds=1)
        if before:
            before = before.created_at
        else:
            before = dt.utcnow()

        # Get the messages
        user_messages = []
        async for message in ctx.channel.history(limit=None, before=before, after=after, oldest_first=True):
            content = message.clean_content
            for z in message.attachments:
                content += f"\n{z.url}"
            user_messages.append((message.author, content))

        # Ask who should be whom
        unique_users = set()
        for u, m in user_messages:
            unique_users.add(u)
        check = lambda m: m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        users_as_characters = {}
        for u in unique_users:
            await ctx.send(f"Who should {u.mention} be portrayed by?")
            while True:
                m = await self.bot.wait_for("message", check=check)
                try:
                    utils.ObjectionFrame.get_character_id(m.content)
                except KeyError:
                    return await ctx.send("I can't work out who that character is meant to be - please run this command later to try again.")
                else:
                    users_as_characters[u] = m.content
                    break

        # Make our data
        frames = [utils.ObjectionFrame(m, users_as_characters[u]) for u, m in user_messages]
        data = [i.to_json() for i in frames]
        string = json.dumps(data)
        encoded = b64encode(string.encode())
        handle = io.StringIO(encoded.decode())
        file = discord.File(handle, filename="objection.objection")
        await ctx.send(file=file)


def setup(bot: vbu.Bot):
    x = PhoenixWrightCommands(bot)
    bot.add_cog(x)
