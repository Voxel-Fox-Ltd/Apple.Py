import string
import random
import typing
import re
import asyncio

import discord
from discord.ext import commands
import voxelbotutils as utils


def create_id(n:int=5):
    """Generates a generic 5 character-string to use as an ID"""

    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=n)).lower()


class QuoteCommands(utils.Cog):

    IMAGE_URL_REGEX = re.compile(r"(http(?:s?):)([/|.|\w|\s|-])*\.(?:jpg|gif|png|jpeg|webp)")
    QUOTE_SEARCH_CHARACTER_CUTOFF = 100

    @utils.group(invoke_without_command=True)
    @commands.bot_has_permissions(send_messages=True, embed_links=True, add_reactions=True)
    @commands.guild_only()
    async def quote(self, ctx:utils.Context, messages:commands.Greedy[discord.Message]):
        """Qutoes a user babeyyyyy lets GO"""

        # Make sure no subcommand is passed
        if ctx.invoked_subcommand is not None:
            return

        # Make sure they have a quote channel
        if self.bot.guild_settings[ctx.guild.id].get('quote_channel_id') is None:
            return await ctx.send("You don't have a quote channel set!")

        # Make sure a message was passed
        if not messages:
            return await ctx.send("I couldn't find any references to messages in your command call.")

        # Recreate the message list without duplicates
        unique_messages = []
        unique_message_ids = set()
        for i in messages:
            if i.id not in unique_message_ids:
                unique_messages.append(i)
            unique_message_ids.add(i.id)
        messages = unique_messages

        # Make sure they're all sent as a reasonable time apart
        quote_is_url = False
        messages = sorted(messages, key=lambda m: m.created_at)
        for i, o in zip(messages, messages[1:]):
            if o is None:
                break
            if (o.created_at - i.created_at).total_seconds() > 3 * 60:
                return await ctx.send("Those messages are too far apart to quote together.")
            if not i.content or i.attachments:
                if len(i.attachments) == 0:
                    return await ctx.send("Embeds can't be quoted.")
                if i.attachments:
                    return await ctx.send("You can't quote multiple messages when quoting images.")

        # Validate the message content
        for message in messages:
            if (quote_is_url and message.content) or (message.content and message.attachments and message.content != message.attachments[0].url):
                return await ctx.send("You can't quote both messages and images.")
            elif message.embeds:
                return await ctx.send("You can't quote embeds.")
            elif len(message.attachments) > 1:
                return await ctx.send("Multiple images can't be quoted.")
            elif message.attachments:
                if self.IMAGE_URL_REGEX.search(message.attachments[0].url) is None:
                    return await ctx.send("The attachment in that image isn't a valid image URL.")
                message.content = message.attachments[0].url
                quote_is_url = True

        # Validate input
        timestamp = messages[0].created_at
        user = messages[0].author
        text = '\n'.join([m.content for m in messages])
        if len(set([i.author.id for i in messages])) != 1:
            return await ctx.send("You can only quote one person at a time.")

        # Make sure they're not quoting themself
        if ctx.author.id in [i.author.id for i in messages] and ctx.author.id not in self.bot.owner_ids:
            return await ctx.send("You can't quote yourself :/")

        # See if it's already been saved
        async with self.bot.database() as db:
            rows = await db(
                "SELECT * FROM user_quotes WHERE guild_id=$1 AND user_id=$2 AND timestamp=$3 AND text=$4",
                ctx.guild.id, user.id, timestamp, text
            )
            if rows:
                return await ctx.send(f"That message has already been quoted with quote ID `{rows[0]['quote_id']}`.")

        # Make embed
        with utils.Embed(use_random_colour=True) as embed:
            embed.set_author_to_user(user)
            if quote_is_url:
                embed.set_image(text)
            else:
                embed.description = text
            # embed.set_footer(text=f"Quote ID {quote_id.upper()}")
            embed.timestamp = timestamp

        # See if we should bother saving it
        async with self.bot.database() as db:
            rows = await db("SELECT * FROM guild_settings WHERE guild_id = $1", ctx.guild.id)
        reactions_needed = rows[0]['quote_reactions_needed']
        ask_to_save_message = await ctx.send(
            f"Should I save this quote? If I receive {reactions_needed} positive reactions in the next 60 seconds, the quote will be saved.",
            embed=embed,
        )
        await ask_to_save_message.add_reaction("\N{THUMBS UP SIGN}")
        await ask_to_save_message.add_reaction("\N{THUMBS DOWN SIGN}")
        await asyncio.sleep(60)

        # Get the message again so we can refresh the reactions
        reaction_count = sum([i.count if str(i.emoji) == "\N{THUMBS UP SIGN}" else -i.count if str(i.emoji) == "\N{THUMBS DOWN SIGN}" else 0 for i in ask_to_save_message.reactions])
        try:
            await ask_to_save_message.delete()
        except discord.HTTPException:
            pass
        if reaction_count < reactions_needed:
            return await ctx.send(f"_Not_ saving the quote asked by {ctx.author.mention} - not enough reactions received.", ignore_error=True)

        # If we get here, we can save to db
        quote_id = create_id()

        # See if they have a quotes channel
        quote_channel_id = self.bot.guild_settings[ctx.guild.id].get('quote_channel_id')
        embed.set_footer(text=f"Quote ID {quote_id.upper()}")
        posted_message = None
        if quote_channel_id:
            channel = self.bot.get_channel(quote_channel_id)
            try:
                posted_message = await channel.send(embed=embed)
            except (discord.Forbidden, AttributeError):
                pass
        if quote_channel_id is None or posted_message is None:
            return await ctx.send("I couldn't send your quote into the quote channel.")

        async with self.bot.database() as db:
            rows = await db(
                "SELECT * FROM user_quotes WHERE guild_id=$1 AND user_id=$2 AND timestamp=$3 AND text=$4",
                ctx.guild.id, user.id, timestamp, text
            )
            if rows:
                return await ctx.send(f"That message has already been quoted with quote ID `{rows[0]['quote_id']}`.")
            await db(
                "INSERT INTO user_quotes (quote_id, guild_id, channel_id, message_id, user_id, timestamp) VALUES ($1, $2, $3, $4, $5, $6)",
                quote_id, ctx.guild.id, posted_message.channel.id, posted_message.id, user.id, timestamp
            )

        # Output to user
        await ctx.send(f"{ctx.author.mention}'s quote request saved with ID `{quote_id.upper()}`", embed=embed, ignore_error=True)

    @quote.command(name="get")
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def quote_get(self, ctx:utils.Context, identifier:commands.clean_content):
        """Gets a quote from the database"""

        # Get quote from database
        async with self.bot.database() as db:
            quote_rows = await db(
                """SELECT user_quotes.quote_id as quote_id, user_id, channel_id, message_id FROM user_quotes LEFT JOIN
                quote_aliases ON user_quotes.quote_id=quote_aliases.quote_id
                WHERE user_quotes.quote_id=$1 OR quote_aliases.alias=$1""",
                identifier.lower(),
            )
        if not quote_rows:
            return await ctx.send(f"There's no quote with the identifier `{identifier.upper()}`.")

        # Get the message
        data = quote_rows[0]
        if data['channel_id'] is None:
            return await ctx.send("There's no quote channel set for that quote.")
        channel = self.bot.get_channel(data['channel_id'])
        if channel is None:
            return await ctx.send("I wasn't able to get your quote channel.")
        try:
            message = await channel.fetch_message(data['message_id'])
            assert message is not None
        except (AssertionError, discord.HTTPException):
            return await ctx.send("I wasn't able to get your quote message.")

        # Output to user
        return await ctx.send(embed=message.embeds[0])

    @quote.command(name="random")
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def quote_random(self, ctx:utils.Context, user:discord.User=None):
        """Gets a random quote for a given user"""

        # Get quote from database
        user = user or ctx.author
        async with self.bot.database() as db:
            quote_rows = await db(
                """SELECT quote_id as quote_id, user_id, channel_id, message_id FROM user_quotes WHERE user_id=$1 ORDER BY RANDOM() LIMIT 1""",
                user.id,
            )
        if not quote_rows:
            return await ctx.send(f"{user.mention} has no available quotes.", allowed_mentions=discord.AllowedMentions.none())

        # Get the message
        data = quote_rows[0]
        if data['channel_id'] is None:
            return await ctx.send("There's no quote channel set for that quote.")
        channel = self.bot.get_channel(data['channel_id'])
        if channel is None:
            return await ctx.send("I wasn't able to get your quote channel.")
        try:
            message = await channel.fetch_message(data['message_id'])
            assert message is not None
        except (AssertionError, discord.HTTPException):
            return await ctx.send("I wasn't able to get your quote message.")

        # Output to user
        return await ctx.send(embed=message.embeds[0])

    @quote.group(name="alias", invoke_without_command=True)
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(send_messages=True)
    async def quote_alias(self, ctx:utils.Context, quote_id:commands.clean_content, alias:commands.clean_content):
        """Adds an alias to a quote"""

        # Grab data from db
        async with self.bot.database() as db:
            rows = await db("SELECT * FROM user_quotes WHERE quote_id=$1", quote_id.lower())
        if not rows:
            return await ctx.send(f"There's no quote with the ID `{quote_id.upper()}`.")

        # Insert alias into db
        async with self.bot.database() as db:
            rows = await db("SELECT * FROM quote_aliases WHERE alias=$1", alias)
            if rows:
                return await ctx.send(f"The alias `{alias}` is already being used.")
            await db("INSERT INTO quote_aliases (quote_id, alias) VALUES ($1, $2)", quote_id.lower(), alias.lower())
        await ctx.send(f"Added the alias `{alias.upper()}` to quote ID `{quote_id.upper()}`.")

    @quote_alias.command(name="remove", aliases=["delete"])
    @commands.has_permissions(manage_guild=True)
    @commands.bot_has_permissions(send_messages=True)
    async def quote_alias_remove(self, ctx:utils.Context, alias:commands.clean_content):
        """Deletes an alias from a quote"""

        # Grab data from db
        async with self.bot.database() as db:
            await db("DELETE FROM quote_aliases WHERE alias=$1", alias.lower())
        return await ctx.send(f"Deleted alias `{alias.upper()}`.")

    @quote.command(name="search", enabled=False)
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def quote_search(self, ctx:utils.Context, user:typing.Optional[discord.Member]=None, *, search_term:str=""):
        """Searches the datbase for a quote with some text in it babeyeyeyey"""

        # Grab data from the database
        async with self.bot.database() as db:
            if user is None:
                rows = await db("SELECT * FROM user_quotes WHERE text LIKE CONCAT('%', $1::text, '%') ORDER BY timestamp DESC LIMIT 10", search_term)
            else:
                rows = await db("SELECT * FROM user_quotes WHERE user_id=$1 AND text LIKE CONCAT('%', $2::text, '%') ORDER BY timestamp DESC LIMIT 10", user.id, search_term)
        if not rows:
            if search_term:
                return await ctx.send("I couldn't find any text matching that pattern.")
            return await ctx.send(f"{(user or ctx.author).mention} hasn't been featured in any quotes.", allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False))

        # Format output
        rows = rows[:10]
        embed = utils.Embed(use_random_colour=True)
        for row in rows:
            if len(row['text']) <= self.QUOTE_SEARCH_CHARACTER_CUTOFF:
                text = row['text']
            else:
                text = f"{row['text'][:self.QUOTE_SEARCH_CHARACTER_CUTOFF]}..."
            embed.add_field(name=row['quote_id'].upper(), value=text, inline=len(text) < 100)
        return await ctx.send(embed=embed, allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False))

    @quote.command(name="delete")
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(send_messages=True)
    async def quote_delete(self, ctx:utils.Context, *quote_ids:str):
        """Deletes a quote from your server"""

        quote_ids = [i.lower() for i in quote_ids]
        quote_channel_id = self.bot.guild_settings[ctx.guild.id].get('quote_channel_id')
        if quote_channel_id:
            quote_channel = self.bot.get_channel(quote_channel_id)
            try:
                async for message in quote_channel.history(limit=150):
                    if not message.author.id == ctx.guild.me.id:
                        continue
                    if not message.embeds:
                        continue
                    embed = message.embeds[0]
                    if not embed.footer:
                        continue
                    footer_text = embed.footer.text
                    if not footer_text:
                        continue
                    if not footer_text.startswith("Quote ID"):
                        continue
                    message_quote_id = footer_text.split(' ')[2].lower()
                    if message_quote_id in quote_ids:
                        try:
                            await message.delete()
                        except discord.HTTPException:
                            pass
            except (discord.HTTPException, AttributeError) as e:
                await ctx.send(e)

        async with self.bot.database() as db:
            await db("DELETE FROM user_quotes WHERE quote_id=ANY($1)", quote_ids)
            # if rows:
            #     await db("DELETE FROM user_quotes WHERE quote_id=$1", quote_id.lower())
        return await ctx.send("Deleted quote(s).")
        # return await ctx.send(f"No quote with ID `{quote_id.upper()}` exists.")


def setup(bot:utils.Bot):
    x = QuoteCommands(bot)
    bot.add_cog(x)
