import asyncio
import re

from bs4 import BeautifulSoup, NavigableString
import discord
from discord.ext import commands
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

    @utils.Cog.listener()
    async def on_message(self, message):
        """
        Sends GitHub/Lab links if a message sent in the server matches the format `gh/user/repo`.
        """

        if (await self.bot.get_context(message)).command is not None:
            return

        # Find matches in the message
        m = re.finditer(r'(?P<ident>g[hl])/(?P<url>(?P<user>\S{1,255})/(?P<repo>\S{1,255}))', message.content)

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

        # Send the GitHub links if there's any output
        if sendable:
            await message.channel.send(sendable)

    @utils.command()
    @commands.bot_has_permissions(send_messages=True, add_reactions=True)
    @commands.is_owner()
    async def addrepoalias(self, ctx:utils.Context, alias:str, repo:str):
        """
        Add a Github repo alias to the database.
        """

        if repo.startswith("gh/"):
            _, owner, repo = repo.split('/')
        elif "github.com" in repo.lower():
            match = re.search(r"(?:https?://)?github\.com/(?P<user>.+)/(?P<repo>.+)", repo)
            if not match:
                raise utils.errors.MissingRequiredArgumentString("repo")
            owner, repo = match.group("user"), match.group("repo")
        else:
            return await ctx.send("I couldn't find that Github repo.")
        async with self.bot.database() as db:
            await db("INSERT INTO github_repo_aliases (alias, owner, repo) VALUES (LOWER($1), $2, $3)", alias, owner, repo)
        await ctx.okay()

    @utils.command()
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
            elif "github.com" in repo.lower():
                match = re.search(r"(?:https?://)?github\.com/(?P<user>.+)/(?P<repo>.+)", repo)
                if not match:
                    raise utils.errors.MissingRequiredArgumentString("repo")
                owner, repo = match.group("user"), match.group("repo")
            else:
                repo_rows = await db("SELECT * FROM github_repo_aliases WHERE alias=LOWER($1)", repo)
                if not repo_rows:
                    return await ctx.send("I couldn't find that Github repo.")
                owner, repo = repo_rows[0]['owner'], repo_rows[0]['repo']

            # See if they have a connected Github account
            user_rows = await db("SELECT * FROM user_settings WHERE user_id=$1", ctx.author.id)
            if not user_rows or not user_rows[0]['github_username']:
                return await ctx.send(f"You need to link your Github account to Discord to run this command - see `{ctx.clean_prefix}website`.")

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
        json = {
            'title': title,
            'body': body,
        }
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'Authorization': f"token {user_rows[0]['github_access_token']}",
        }
        async with self.bot.session.post(f"https://api.github.com/repos/{owner}/{repo}/issues", json=json, headers=headers) as r:
            if str(r.status)[0] != '2':
                return await ctx.send("I was unable to create an issue on that repository.")
            data = await r.json()
            self.logger.info(f"Received data from Github - {data!s}")

        # And done
        await ctx.send(f"Your issue has been created - <{data['html_url']}>.")

    @utils.Cog.listener("on_message")
    async def github_message_answer_listener(self, message:discord.Message):
        """
        Listens for messages being made and finds Github answer URLs in them.
        """

        # Set up our filters
        if not message.guild:
            return
        if not self.bot.guild_settings[message.guild.id]['dump_stackoverflow_answers']:
            return
        if not message.channel.permissions_for(message.guild.me).send_messages:
            return
        if not message.channel.permissions_for(message.guild.me).embed_links:
            return
        if (await self.bot.get_context(message)).command is not None:
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
