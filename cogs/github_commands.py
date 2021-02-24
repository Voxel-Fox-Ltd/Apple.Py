import asyncio
import re
from urllib.parse import quote

from discord.ext import commands
import voxelbotutils as utils


class GithubCommands(utils.Cog):

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
        m = re.finditer(r'(?P<ident>g[hl])/(?P<url>(?P<user>\S{1,255})/(?P<repo>\S{1,255}))', message.content)
        n = re.finditer(r'(?P<ident>g[hl]) (?P<alias>\S{1,255})', message.content)

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
            await message.channel.send(sendable)

    @utils.command()
    @utils.checks.is_bot_support()
    @commands.bot_has_permissions(send_messages=True, add_reactions=True)
    async def addrepoalias(self, ctx:utils.Context, alias:str, repo:str):
        """
        Add a Github repo alias to the database.
        """

        if repo.startswith("gh/"):
            _, owner, repo = repo.split('/')
            host = "Github"
        elif "github.com" in repo.lower():
            match = re.search(r"(?:https?://)?github\.com/(?P<user>.+)/(?P<repo>.+)", repo)
            owner, repo = match.group("user"), match.group("repo")
            host = "Github"
        elif repo.startswith("gl/"):
            _, owner, repo = repo.split('/')
            host = "Gitlab"
        elif "gitlab.com" in repo.lower():
            match = re.search(r"(?:https?://)?gitlab\.com/(?P<user>.+)/(?P<repo>.+)", repo)
            owner, repo = match.group("user"), match.group("repo")
            host = "Gitlab"
        else:
            return await ctx.send("I couldn't find that git repo.")
        async with self.bot.database() as db:
            await db("INSERT INTO github_repo_aliases (alias, owner, repo, host) VALUES (LOWER($1), $2, $3, $4)", alias, owner, repo, host)
        await ctx.okay()

    @utils.command(aliases=['ci'])
    @commands.bot_has_permissions(send_messages=True, embed_links=True, add_reactions=True)
    async def createissue(self, ctx:utils.Context, repo:str, *, title:str):
        """
        Create a Github issue on a given repo.
        """

        # Get the database because whatever why not
        async with self.bot.database() as db:

            # Validate the repo
            if repo.startswith("gh/"):
                _, owner, repo = repo.split('/')
                host = "Github"
            elif "github.com" in repo.lower():
                match = re.search(r"(?:https?://)?github\.com/(?P<user>.+)/(?P<repo>.+)", repo)
                owner, repo = match.group("user"), match.group("repo")
                host = "Github"
            elif repo.startswith("gl/"):
                _, owner, repo = repo.split('/')
                host = "Gitlab"
            elif "gitlab.com" in repo.lower():
                match = re.search(r"(?:https?://)?github\.com/(?P<user>.+)/(?P<repo>.+)", repo)
                owner, repo = match.group("user"), match.group("repo")
                host = "Gitlab"
            else:
                repo_rows = await db("SELECT * FROM github_repo_aliases WHERE alias=LOWER($1)", repo)
                if not repo_rows:
                    return await ctx.send("I couldn't find that git repo.")
                owner, repo, host = repo_rows[0]['owner'], repo_rows[0]['repo'], repo_rows[0]['host']

            # See if they have a connected Github account
            user_rows = await db("SELECT * FROM user_settings WHERE user_id=$1", ctx.author.id)
            if not user_rows or not user_rows[0][f'{host.lower()}_username']:
                return await ctx.send(f"You need to link your {host} account to Discord to run this command - see `{ctx.clean_prefix}website`.")

        # Ask if we want to do this
        embed = utils.Embed(title=title, use_random_colour=True).set_footer("Use the \N{HEAVY PLUS SIGN} emoji to add a body.")
        m = await ctx.send("Are you sure you want to create this issue?", embed=embed)
        valid_emojis = ["\N{THUMBS UP SIGN}", "\N{HEAVY PLUS SIGN}", "\N{THUMBS DOWN SIGN}"]
        for e in valid_emojis:
            self.bot.loop.create_task(m.add_reaction(e))
        try:
            check = lambda p: p.message_id == m.id and str(p.emoji) in valid_emojis and p.user_id == ctx.author.id
            payload = await self.bot.wait_for("raw_reaction_add", check=check, timeout=120)
        except asyncio.TimeoutError:
            return await ctx.send("Timed out asking for issue create confirmation.")

        # Get the body
        body = None
        if str(payload.emoji) == "\N{HEAVY PLUS SIGN}":
            m = await ctx.send("What body content do you want to be added to your issue?")
            try:
                check = lambda m: m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
                body_message = await self.bot.wait_for("message", check=check, timeout=60 * 5)
            except asyncio.TimeoutError:
                return await ctx.send("Timed out asking for issue body text.")
            body = body_message.content

        if body:
            embed = utils.Embed(title=title, description=body, use_random_colour=True)
            m = await ctx.send("Are you sure you want to create this issue?", embed=embed)
            valid_emojis = ["\N{THUMBS UP SIGN}", "\N{THUMBS DOWN SIGN}"]
            for e in valid_emojis:
                self.bot.loop.create_task(m.add_reaction(e))
            try:
                check = lambda p: p.message_id == m.id and str(p.emoji) in valid_emojis and p.user_id == ctx.author.id
                payload = await self.bot.wait_for("raw_reaction_add", check=check, timeout=120)
            except asyncio.TimeoutError:
                return await ctx.send("Timed out asking for issue create confirmation.")

        # Check the reaction
        if str(payload.emoji) == "\N{THUMBS DOWN SIGN}":
            return await ctx.send("Alright, cancelling issue add.")

        # Create the issue
        if host == "Github":
            json = {'title': title, 'body': body}
            headers = {
                'Accept': 'application/vnd.github.v3+json',
                'Authorization': f"token {user_rows[0]['github_access_token']}",
            }
            async with self.bot.session.post(f"https://api.github.com/repos/{owner}/{repo}/issues", json=json, headers=headers) as r:
                data = await r.json()
                self.logger.info(f"Received data from Github {r.url!s} - {data!s}")
                if str(r.status)[0] != '2':
                    return await ctx.send(f"I was unable to create an issue on that Github repository - `{data}`.")
            await ctx.send(f"Your issue has been created - <{data['html_url']}>.")
        elif host == "Gitlab":
            json = {'title': title, 'description': body}
            headers = {
                'Authorization': f"Bearer {user_rows[0]['gitlab_bearer_token']}",
            }
            async with self.bot.session.post(f"https://gitlab.com/api/v4/projects/{quote(owner + '/' + repo, safe='')}/issues", json=json, headers=headers) as r:
                data = await r.json()
                self.logger.info(f"Received data from Gitlab {r.url!s} - {data!s}")
                if str(r.status)[0] != '2':
                    return await ctx.send(f"I was unable to create an issue on that Gitlab repository - `{data}`.")
            await ctx.send(f"Your issue has been created - <{data['web_url']}>.")


def setup(bot:utils.Bot):
    x = GithubCommands(bot)
    bot.add_cog(x)
