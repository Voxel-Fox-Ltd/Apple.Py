import re
import collections

from discord.ext import tasks
import voxelbotutils as utils


class DiscordDatamining(utils.Cog):

    DISCORD_DOCS_API_REPO_URL = "https://api.github.com/repos/discord/discord-api-docs/commits"
    DISCORD_DOCS_REPO_URL = "https://github.com/discord/discord-api-docs/"

    DISCORD_DATAMINING_API_REPO_URL = "https://api.github.com/repos/DJScias/Discord-Datamining/commits"
    DISCORD_DATAMINING_REPO_URL = "https://github.com/DJScias/Discord-Datamining/"

    VFL_CODING_CHANNEL_ID = 760664929593851925

    def __init__(self, bot:utils.Bot):
        super().__init__(bot)
        self.last_posted_commit = collections.defaultdict(lambda: None)
        self.docs_commit_poster_loop.start("New Discord Docs Info", self.DISCORD_DOCS_API_REPO_URL, self.DISCORD_DOCS_REPO_URL)
        self.datamining_commit_poster_loop.start("New Discord Client Data", self.DISCORD_DATAMINING_API_REPO_URL, self.DISCORD_DATAMINING_REPO_URL)

    def cog_unload(self):
        self.datamining_commit_poster_loop.stop()
        self.docs_commit_poster_loop.stop()

    @tasks.loop(minutes=15)
    async def datamining_commit_poster_loop(self, embed_title:str, api_url:str, repo_url:str):
        await self.commit_poster_loop(embed_title, api_url, repo_url)

    @datamining_commit_poster_loop.before_loop
    async def before_datamining_commit_poster_loop(self):
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=15)
    async def docs_commit_poster_loop(self, embed_title:str, api_url:str, repo_url:str):
        await self.commit_poster_loop(embed_title, api_url, repo_url)

    @docs_commit_poster_loop.before_loop
    async def before_docs_commit_poster_loop(self):
        await self.bot.wait_until_ready()

    async def commit_poster_loop(self, embed_title:str, api_url:str, repo_url:str):
        """Grab the data from the Discord datamining repo and post it to the coding channel of VFL"""

        # Grab the data
        self.logger.info(f"Grabbing repo data from {api_url}")
        async with self.bot.session.get(api_url) as r:
            data = await r.json()

        # Let's work out the new data
        new_commits = []
        if self.last_posted_commit[repo_url] is None:
            self.last_posted_commit[repo_url] = data[0]['sha']
            self.logger.info("Setting to last commit - no commits cached")
            return
        for index, i in enumerate(data):
            if i['sha'] == self.last_posted_commit[repo_url]:
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
            embed.title = embed_title
            embed.description = '\n'.join([f"{i['commit']['message']} - [Link]({repo_url}commit/{i['sha']})" for i in new_commits])
            for sha, body in comment_text:
                embed.add_field(sha, body, inline=False)

        # And send
        channel = self.bot.get_channel(self.VFL_CODING_CHANNEL_ID)
        m = await channel.send(embed=embed)
        await m.publish()
        self.logger.info("Sent data to channel")
        self.last_posted_commit[repo_url] = new_commits[0]['sha']


def setup(bot:utils.Bot):
    x = DiscordDatamining(bot)
    bot.add_cog(x)
