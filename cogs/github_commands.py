import re

from bs4 import BeautifulSoup, NavigableString
import discord
import voxelbotutils as utils


class GithubCommands(utils.Cog):

    GITHUB_ANSWER_URL_REGEX = re.compile(r"https?://stackoverflow\.com/a/(?P<answerid>\d+)")
    GITHUB_ANSWER_API_URL = "https://api.stackexchange.com/2.2/answers/{answer_id}"
    GITHUB_ANSWER_API_PARAMS = {
        'order': 'desc',
        'sort': 'activity',
        'site': 'stackoverflow',
        'filter': '!)Q29mwsOXXJEzlkx48kegp4T',
    }

    @utils.Cog.listener("on_message")
    async def github_message_answer_listener(self, message:discord.Message):
        """Listens for messages being made and finds Github answer URLs in them"""

        # Set up our filters
        if not message.guild:
            return
        if not self.bot.guild_settings[message.guild.id]['dump_stackoverflow_answers']:
            return
        if not message.channel.permissions_for(message.guild.me).send_messages:
            return
        if not message.channel.permissions_for(message.guild.me).embed_links:
            return
        matches = self.GITHUB_ANSWER_URL_REGEX.search(message.content)
        if not matches:
            return

        # Get vars
        github_answer_id = matches.group('answerid')
        async with self.bot.session.get(self.GITHUB_ANSWER_API_URL.format(answer_id=github_answer_id), params=self.GITHUB_ANSWER_API_PARAMS) as r:
            data = await r.json()
        answer = data['items'][0]['body']

        # Build the output
        output = []
        soup = BeautifulSoup(answer, 'html.parser')
        for child in soup.children:
            if isinstance(child, (str, NavigableString)):
                output.append(str(child))
                continue
            elif child.name == "pre":
                output.append(f"```\n{child.text}```")
                continue
            builder = ""
            for nested_child in child.children:
                if isinstance(nested_child, (str, NavigableString)):
                    builder += nested_child
                else:
                    if nested_child.name == "code":
                        builder += f"`{nested_child.text}`"
                    elif nested_child.name == "a":
                        builder += f"[{nested_child.text}]({nested_child['href']})"
                    else:
                        builder += str(nested_child)
            output.append(builder)

        # Format the data
        embed = utils.Embed(use_random_colour=True, description='\n'.join(output).replace('\n\n', '\n'))
        try:
            await message.edit(suppress=True)
        except discord.Forbidden:
            pass
        await message.channel.send(embed=embed)


def setup(bot:utils.Bot):
    x = GithubCommands(bot)
    bot.add_cog(x)
