import re

import voxelbotutils as utils


class GitText(utils.Cog):

    @utils.Cog.listener()
    async def on_message(self, message):
        """
        Sends GitHub/Lab links if a message sent in the server matches the format `gh/user/repo`.
        """

        # Find matches in the message
        m = re.finditer(r'(?P<ident>g[hl])/(?P<url>(?P<user>\S{1,255})/(?P<repo>\S{1,255}))', message.content)
        
        # Dictionary of possible Git() links
        git_dict = {
            "h": "hub",
            "l": "lab"
        }
        
        # Add the url of each matched link to the final output
        sendable = ""
        for i in m:
            url = i.group("url")
            ident = i.group("ident")
            sendable += f"<https://git{git_dict[ident]}.com/{url}>\n"

        # Send the GitHub links if there's any output
        if sendable:
            await message.channel.send(sendable)


def setup(bot:utils.Bot):
    x = GitText(bot)
    bot.add_cog(x)
