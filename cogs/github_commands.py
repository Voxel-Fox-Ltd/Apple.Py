import asyncio
import re
from urllib.parse import quote
import math

import asyncpg
import discord
from discord.ext import commands
import voxelbotutils as utils


class GitRepo(object):

    __slots__ = ('host', 'owner', 'repo')

    def __init__(self, host, owner, repo):
        self.host = host
        self.owner = owner
        self.repo = repo

    @property
    def html_url(self):
        if self.host == "Github":
            return f"https://github.com/{self.owner}/{self.repo}"
        return f"https://gitlab.com/{self.owner}/{self.repo}"

    @property
    def issue_api_url(self):
        if self.host == "Github":
            return f"https://api.github.com/repos/{self.owner}/{self.repo}/issues"
        return f"https://gitlab.com/api/v4/projects/{quote(self.owner + '/' + self.repo, safe='')}/issues"

    @property
    def issue_comments_api_url(self):
        if self.host == "Github":
            return f"https://api.github.com/repos/{self.owner}/{self.repo}/issues/{{issue}}/comments"
        return f"https://gitlab.com/api/v4/projects/{quote(self.owner + '/' + self.repo, safe='')}/issues/{{issue}}/notes"

    @classmethod
    async def convert(cls, ctx:utils.Context, value:str):
        """
        Convert a string into an (host, owner, repo) string tuple.
        """

        value = value.rstrip('/')
        if value.startswith("gh/"):
            _, owner, repo = value.split('/')
            host = "Github"
        elif "github.com" in value.lower():
            match = re.search(r"(?:https?://)?github\.com/(?P<user>[a-zA-Z0-9_\-.]+)/(?P<repo>[a-zA-Z0-9_\-.]+)", value)
            owner, repo = match.group("user"), match.group("repo")
            host = "Github"
        elif value.startswith("gl/"):
            _, owner, repo = value.split('/')
            host = "Gitlab"
        elif "gitlab.com" in value.lower():
            match = re.search(r"(?:https?://)?gitlab\.com/(?P<user>[a-zA-Z0-9_\-.]+)/(?P<repo>[a-zA-Z0-9_\-.]+)", value)
            owner, repo = match.group("user"), match.group("repo")
            host = "Gitlab"
        else:
            async with ctx.bot.database() as db:
                repo_rows = await db("SELECT * FROM github_repo_aliases WHERE alias=LOWER($1)", value)
            if not repo_rows:
                raise commands.BadArgument("I couldn't find that git repo.")
            owner, repo, host = repo_rows[0]['owner'], repo_rows[0]['repo'], repo_rows[0]['host']
        return cls(host, owner, repo)


class GitIssueNumber(int):

    @classmethod
    async def convert(cls, ctx:utils.Context, value:str):
        value = value.lstrip('#')
        return cls(value)


class GithubCommands(utils.Cog):

    GIT_ISSUE_OPEN_EMOJI = "<:github_issue_open:817984658456707092>"
    GIT_ISSUE_CLOSED_EMOJI = "<:github_issue_closed:817984658372689960>"

    @utils.Cog.listener()
    async def on_message(self, message):
        """
        Sends GitHub/Lab links if a message sent in the server matches the format `gh/user/repo`.
        """

        if message.author.bot:
            return
        if (await self.bot.get_context(message)).command is not None:
            return

        # Find matches in the message
        m = re.finditer(r'\b(?P<ident>g[hl])/(?P<url>(?P<user>\S{1,255})/(?P<repo>\S{1,255}))\b', message.content)
        n = re.finditer(r'\b(?P<ident>g[hl]) (?P<alias>\S{1,255})\b', message.content)

        # Dictionary of possible Git() links
        git_dict = {
            "gh": "hub",
            "gl": "lab"
        }

        # Add the url of each matched link to the final output
        sendable = ""
        for i in m:
            url = i.group("url")
            ident = i.group("ident")
            sendable += f"<https://git{git_dict[ident]}.com/{url}>\n"
        if n:
            async with self.bot.database() as db:
                for i in n:
                    rows = await db("SELECT * FROM github_repo_aliases WHERE alias=$1", i.group("alias"))
                    if rows:
                        sendable += f"<https://{rows[0]['host'].lower()}.com/{rows[0]['owner']}/{rows[0]['repo']}>\n"

        # Send the GitHub links if there's any output
        if sendable:
            await message.channel.send(sendable, allowed_mentions=discord.AllowedMentions.none())

    @utils.group()
    async def repoalias(self, ctx:utils.Context):
        """
        The parent command for handling git repo aliases.
        """

        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @repoalias.command(name="add")
    @commands.bot_has_permissions(send_messages=True, add_reactions=True)
    async def repoalias_add(self, ctx:utils.Context, alias:str, repo:GitRepo):
        """
        Add a Github repo alias to the database.
        """

        async with self.bot.database() as db:
            try:
                await db(
                    """INSERT INTO github_repo_aliases (alias, owner, repo, host, added_by)
                    VALUES (LOWER($1), $2, $3, $4, $5)""",
                    alias, repo.owner, repo.repo, repo.host, ctx.author.id,
                )
            except asyncpg.UniqueViolationError:
                data = await db("SELECT * FROM github_repo_aliases WHERE alias=LOWER($1) AND added_by=$2", alias, ctx.author.id)
                if not data:
                    return await ctx.send(f"The alias `{alias.lower()}` is already in use.", allowed_mentions=discord.AllowedMentions.none())
                await db("DELETE FROM github_repo_aliases WHERE alias=$1", alias)
                return await ctx.invoke(ctx.command, alias, repo)
        await ctx.okay()

    @repoalias.command(name="remove", aliases=['delete', 'del', 'rem'])
    @commands.bot_has_permissions(send_messages=True, add_reactions=True)
    async def repoalias_remove(self, ctx:utils.Context, alias:str):
        """
        Removes a Github repo alias from the database.
        """

        async with self.bot.database() as db:
            data = await db("SELECT * FROM github_repo_aliases WHERE alias=LOWER($1) AND added_by=$2", alias, ctx.author.id)
            if not data:
                return await ctx.send("You don't own that repo alias.", allowed_mentions=discord.AllowedMentions.none())
            await db("DELETE FROM github_repo_aliases WHERE alias=LOWER($1)", alias)
        await ctx.okay()

    @utils.command(aliases=['ci'], hidden=True)
    @commands.bot_has_permissions(send_messages=True, embed_links=True, add_reactions=True)
    async def createissue(self, ctx:utils.Context, repo:GitRepo, *, title:str):
        """
        Create a Github issue on a given repo.
        """

        return await ctx.invoke(self.bot.get_command("issue create"), repo, title=title)

    @utils.group(aliases=['issues'])
    @commands.bot_has_permissions(send_messages=True, embed_links=True, add_reactions=True)
    async def issue(self, ctx:utils.Context):
        """
        The parent group for the git issue commands.
        """

        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @issue.command(name='create', aliases=['make'])
    @commands.bot_has_permissions(send_messages=True, embed_links=True, add_reactions=True)
    async def issue_create(self, ctx:utils.Context, repo:GitRepo, *, title:str):
        """
        Create a Github issue on a given repo.
        """

        # Get the database because whatever why not
        async with self.bot.database() as db:
            user_rows = await db("SELECT * FROM user_settings WHERE user_id=$1", ctx.author.id)
            if not user_rows or not user_rows[0][f'{repo.host.lower()}_username']:
                return await ctx.send(f"You need to link your {repo.host} account to Discord to run this command - see `{ctx.clean_prefix}website`.")

        # Ask if we want to do this
        embed = utils.Embed(title=title, use_random_colour=True).set_footer("Use the \N{HEAVY PLUS SIGN} emoji to add a body.")
        m = await ctx.send("Are you sure you want to create this issue?", embed=embed)
        valid_emojis = ["\N{THUMBS UP SIGN}", "\N{HEAVY PLUS SIGN}", "\N{THUMBS DOWN SIGN}"]
        body = None
        while True:
            if body:
                embed = utils.Embed(
                    title=title, description=body, use_random_colour=True
                ).set_footer("Use the \N{HEAVY PLUS SIGN} emoji to change the body.")
            else:
                for e in valid_emojis:
                    self.bot.loop.create_task(m.add_reaction(e))
            try:
                check = lambda p: p.message_id == m.id and str(p.emoji) in valid_emojis and p.user_id == ctx.author.id
                payload = await self.bot.wait_for("raw_reaction_add", check=check, timeout=120)
            except asyncio.TimeoutError:
                return await ctx.send("Timed out asking for issue create confirmation.")

            # Get the body
            if str(payload.emoji) == "\N{HEAVY PLUS SIGN}":
                n = await ctx.send("What body content do you want to be added to your issue?")
                try:
                    check = lambda n: n.author.id == ctx.author.id and n.channel.id == ctx.channel.id
                    body_message = await self.bot.wait_for("message", check=check, timeout=60 * 5)
                except asyncio.TimeoutError:
                    return await ctx.send("Timed out asking for issue body text.")
                try:
                    await n.delete()
                    await body_message.delete()
                except discord.HTTPException:
                    pass
                try:
                    await m.remove_reaction("\N{HEAVY PLUS SIGN}", ctx.author)
                except discord.HTTPException:
                    pass
                body = body_message.content

                embed = utils.Embed(title=title, description=body, use_random_colour=True)
                await m.edit(contnet="Are you sure you want to create this issue?", embed=embed)

            # Check the reaction
            if str(payload.emoji) == "\N{THUMBS DOWN SIGN}":
                return await ctx.send("Alright, cancelling issue add.")
            if str(payload.emoji) == "\N{THUMBS UP SIGN}":
                break

        # Work out our args
        if repo.host == "Github":
            json = {'title': title, 'body': body}
            headers = {'Accept': 'application/vnd.github.v3+json', 'Authorization': f"token {user_rows[0]['github_access_token']}"}
        elif repo.host == "Gitlab":
            json = {'title': title, 'description': body}
            headers = {'Authorization': f"Bearer {user_rows[0]['gitlab_bearer_token']}"}
        headers.update({'User-Agent': self.bot.user_agent})

        # Make the post request
        async with self.bot.session.post(repo.issue_api_url, json=json, headers=headers) as r:
            data = await r.json()
            self.logger.info(f"Received data from git {r.url!s} - {data!s}")
            if 200 <= r.status < 300:
                pass
            else:
                return await ctx.send(f"I was unable to create an issue on that repository - `{data}`.")
        await ctx.send(f"Your issue has been created - <{data.get('html_url') or data.get('web_url')}>.")

    @issue.command(name="list")
    async def issue_list(self, ctx:utils.Context, repo:GitRepo, list_closed:bool=False):
        """
        List all of the issues on a git repo.
        """

        # Get the database because whatever why not
        async with self.bot.database() as db:
            user_rows = await db("SELECT * FROM user_settings WHERE user_id=$1", ctx.author.id)
            if not user_rows or not user_rows[0][f'{repo.host.lower()}_username']:
                return await ctx.send(f"You need to link your {repo.host} account to Discord to run this command - see `{ctx.clean_prefix}website`.")

        # Get the issues
        if repo.host == "Github":
            params = {'state': 'all' if list_closed else 'open'}
            headers = {'Accept': 'application/vnd.github.v3+json', 'Authorization': f"token {user_rows[0]['github_access_token']}"}
        elif repo.host == "Gitlab":
            params = {'state': 'opened'}
            if list_closed:
                params.pop('state', None)
            headers = {'Authorization': f"Bearer {user_rows[0]['gitlab_bearer_token']}"}

        async with self.bot.session.get(repo.issue_api_url, params=params, headers=headers) as r:
            data = await r.json()
            self.logger.info(f"Received data from git {r.url!s} - {data!s}")
            if 200 <= r.status < 300:
                pass
            else:
                return await ctx.send(f"I was unable to get the issues on that repository - `{data}`.")
        if len(data) == 0:
            return await ctx.send("There are no issues in the repository!")
        # Format the lines
        output = []
        PER_PAGE = 8
        for index, issue in enumerate(data):
            if issue.get("pull_request"):
                continue
            if repo.host == "Github":
                issue_id = str(issue.get('number'))
                url = issue.get('html_url')
            elif repo.host == "Gitlab":
                issue_id = str(issue.get('iid'))
                url = issue.get('web_url')
            title = issue.get('title')
            if list_closed:
                max_title_length = math.floor(2000 / PER_PAGE) - len(issue_id) - len(url) - 11 - 41  # 11 refers to the linking characters, 41 the emoji
                if len(title) > max_title_length:
                    title = title[:max_title_length].rstrip() + '...'
                output.append(f"* {self.GIT_ISSUE_OPEN_EMOJI if issue.get('state').startswith('open') else self.GIT_ISSUE_CLOSED_EMOJI} (#{issue_id}) [{title}]({url})")
            else:
                max_title_length = math.floor(2000 / PER_PAGE) - len(issue_id) - len(url) - 11  # 11 refers to the linking characters
                if len(title) > max_title_length:
                    title = title[:max_title_length].rstrip() + '...'
                output.append(f"* (#{issue_id}) [{title}]({url})")

        # Output as paginator
        return await utils.Paginator(output, per_page=PER_PAGE).start(ctx)

    @issue.command(name="comment")
    async def issue_comment(self, ctx:utils.Context, repo:GitRepo, issue:GitIssueNumber, *, comment:str):
        """
        Comment on a git issue.
        """

        # Get the database because whatever why not
        async with self.bot.database() as db:
            user_rows = await db("SELECT * FROM user_settings WHERE user_id=$1", ctx.author.id)
            if not user_rows or not user_rows[0][f'{repo.host.lower()}_username']:
                return await ctx.send(f"You need to link your {repo.host} account to Discord to run this command - see `{ctx.clean_prefix}website`.")

        # Get the headers
        if repo.host == "Github":
            headers = {'Accept': 'application/vnd.github.v3+json','Authorization': f"token {user_rows[0]['github_access_token']}",}
        elif repo.host == "Gitlab":
            headers = {'Authorization': f"Bearer {user_rows[0]['gitlab_bearer_token']}"}
        json = {'body': comment}
        headers.update({'User-Agent': self.bot.user_agent})

        # Create comment
        async with self.bot.session.post(repo.issue_comments_api_url.format(issue=issue), json=json, headers=headers) as r:
            data = await r.json()
            self.logger.info(f"Received data from git {r.url!s} - {data!s}")
            if r.status == 404:
                return await ctx.send("I was unable to find that issue.")
            if 200 <= r.status < 300:
                pass
            else:
                return await ctx.send(f"I was unable to create a comment on that issue - `{data}`.")

        # Output
        if repo.host == "Github":
            return await ctx.send(f"Comment added! <{data['html_url']}>")
        return await ctx.send(f"Comment added! <https://gitlab.com/{repo.owner}/{repo.repo}/-/issues/{issue}#note_{data['id']}>")

    @issue.command(name="close", enabled=False)
    async def issue_close(self, ctx:utils.Context, repo:GitRepo, issue:GitIssueNumber):
        """
        Close a git issue.
        """

        # Get the database because whatever why not
        host, owner, repo = repo
        async with self.bot.database() as db:
            user_rows = await db("SELECT * FROM user_settings WHERE user_id=$1", ctx.author.id)
            if not user_rows or not user_rows[0][f'{host.lower()}_username']:
                return await ctx.send(f"You need to link your {host} account to Discord to run this command - see `{ctx.clean_prefix}website`.")

        # Get the issues
        if host == "Github":
            json = {'state': 'closed'}
            headers = {
                'Accept': 'application/vnd.github.v3+json',
                'Authorization': f"token {user_rows[0]['github_access_token']}",
                'User-Agent': self.bot.user_agent,
            }
            async with self.bot.session.post(f"https://api.github.com/repos/{owner}/{repo}/issues/{issue}", json=json, headers=headers) as r:
                data = await r.json()
                self.logger.info(f"Received data from Github {r.url!s} - {data!s}")
                if 200 <= r.status < 300:
                    pass
                else:
                    return await ctx.send(f"I was unable to get the issues on that Github repository - `{data}`.")
        elif host == "Gitlab":
            json = {'state_event': 'close'}
            headers = {
                'Authorization': f"Bearer {user_rows[0]['gitlab_bearer_token']}",
                'User-Agent': self.bot.user_agent,
            }
            async with self.bot.session.post(f"https://gitlab.com/api/v4/projects/{quote(owner + '/' + repo, safe='')}/issues/{issue}", json=json, headers=headers) as r:
                data = await r.json()
                self.logger.info(f"Received data from Gitlab {r.url!s} - {data!s}")
                if 200 <= r.status < 300:
                    pass
                else:
                    return await ctx.send(f"I was unable to get the issues on that Gitlab repository - `{data}`.")
        return await ctx.send("Issue closed.")


def setup(bot:utils.Bot):
    x = GithubCommands(bot)
    bot.add_cog(x)
