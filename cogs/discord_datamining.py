import re

from discord.ext import tasks

from cogs import utils


class DiscordDatamining(utils.Cog):

    DISCORD_DATAMINING_API_REPO_URL = "https://api.github.com/repos/DJScias/Discord-Datamining/commits"
    DISCORD_DATAMINING_REPO_URL = "https://github.com/DJScias/Discord-Datamining/"
    VFL_CODING_CHANNEL_ID = 636085718002958336

    def __init__(self, bot:utils.Bot):
        super().__init__(bot)
        self.last_posted_commit = None
        self.commit_poster_loop.start()

    def cog_unload(self):
        self.commit_poster_loop.stop()

    @tasks.loop(minutes=15)
    async def commit_poster_loop(self):
        """Grab the data from the Discord datamining repo and post it to the coding channel of VFL"""

        # Grab the data
        self.logger.info("Grabbing repo data")
        async with self.bot.session.get(self.DISCORD_DATAMINING_API_REPO_URL) as r:
            data = await r.json()

        # Let's work out the new data
        new_commits = []
        if self.last_posted_commit is None:
            self.last_posted_commit = data[0]['sha']
            self.logger.info("Setting to last commit - no commits cached")
            return
        for index, i in enumerate(data):
            if i['sha'] == self.last_posted_commit:
                new_commits = data[:index]
                break

        # See if we have anything to talk about
        if not new_commits:
            self.logger.info("No new commits found")
            return
        self.logger.info(f"Logging info of {len(new_commits)} commits")

        # Work out which of our new commits have comments
        comment_urls = [i['comments_url'] for i in new_commits if i['commit']['comment_count'] > 0]
        comment_text = []
        for url in comment_urls:
            async with self.bot.session.get(url) as r:
                data = await r.json()
            comment_text.extend([(i['commit_id'], re.sub(r"^## (.+)", r"**\1**", i['body'])) for i in data])
        self.logger.info(f"Logging info of {len(comment_text)} comments")

        # Format it all into an embed
        with utils.Embed(use_random_colour=True) as embed:
            embed.title = "New Discord Client Data"
            embed.description = '\n'.join([f"{i['commit']['message']} - [Link]({self.DISCORD_DATAMINING_REPO_URL}/commit/{i['sha']})" for i in new_commits])
            for sha, body in comment_text:
                embed.add_field(sha, body, inline=False)

        # And send
        channel = self.bot.get_channel(self.VFL_CODING_CHANNEL_ID)
        await channel.send(embed=embed)
        self.logger.info("Sent data to channel")
        self.last_posted_commit = new_commits[0]['sha']

    @commit_poster_loop.before_loop
    async def before_commit_poster_loop(self):
        await self.bot.wait_until_ready()


def setup(bot:utils.Bot):
    x = DiscordDatamining(bot)
    bot.add_cog(x)
