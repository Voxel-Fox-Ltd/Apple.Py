import re

import voxelbotutils as utils
import discord

class GHText(utils.Cog):

  @utils.Cog.listener()
  async def on_message(self, message):
    '''Sends GitHub links if a message sent in the server matches the format `gh/user/repo`'''
    
    # Find matches in the message
    m = re.finditer(r'gh/(?P<url>(?P<user>\S{1,39})/(?P<repo>\S{1,100}))', message.content)
    
    # Add the url of each matched link to the final output
    sendable = ""
    for i in m:
      url = i.group("url")
      sendable += f"<https://github.com/{url}>\n"
    
    # Send the GitHub links if there's any output
    if sendable:
      await ctx.send(sendable)


def setup(bot:utils.Bot):
    x = GHText(bot)
    bot.add_cog(x)
