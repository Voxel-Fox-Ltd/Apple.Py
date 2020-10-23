import discord
from discord.ext import commands
import voxelbotutils as utils


class BotInfo(utils.Cog):

    @utils.command()
    async def botinfo(self, ctx:utils.Context, bot:discord.User):
        """Gives you information about a bot"""

        if bot.bot is False:
            return await ctx.send("That isn't even a bot.")

        bot_info = [i for i in self.bot.config['bot_info'] if i['user_id'] == bot.id]
        if not bot_info:
            return await ctx.send(f"I don't have any information on record about {bot.mention}.")
        bot_info = bot_info[0]

        with utils.Embed(use_random_colour=True) as embed:
            embed.set_author_to_user(user=bot)
            embed.description = bot_info['description']
            for field in bot_info.get('fields', list()):
                embed.add_field(name=field['name'], value=field['value'], inline=field.get('inline', False))
            embed.set_thumbnail(url=bot.avatar_url)
            if bot_info.get('image'):
                embed.set_image(url=bot_info['image'])
        return await ctx.send(embed=embed)


def setup(bot:utils.Bot):
    x = BotInfo(bot)
    bot.add_cog(x)
