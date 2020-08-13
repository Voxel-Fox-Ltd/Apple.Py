import string
import random
import typing

import discord
from discord.ext import commands

from cogs import utils


def create_id(n:int=5):
    """Generates a generic 5 character-string to use as an ID"""

    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=n)).lower()


class QuoteCommands(utils.Cog):

    @commands.group(cls=utils.Group)
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    @commands.guild_only()
    async def quote(self, ctx:utils.Context, messages:commands.Greedy[discord.Message]):
        """Qutoes a user babeyyyyy lets GO"""

        # Make sure no subcommand is passed
        if ctx.invoked_subcommand is not None:
            return

        # Make sure a message was passed
        if not messages:
            return await ctx.send("I couldn't find any references to messages in your command call.")

        # Make sure they're all sent as a reasonable time apart
        messages = sorted(messages, key=lambda m: m.created_at)
        for i, o in zip(messages, messages[1:]):
            if o is None:
                break
            if (o.created_at - i.created_at).total_seconds() > 3 * 60:
                return await ctx.send("Those messages are too far apart to quote together.")
            if not i.content or i.attachments:
                return await ctx.send("Images can't be quoted.")
        if not messages[0].content or messages[0].attachments:
            return await ctx.send("Images can't be quoted.")

        # Validate input
        timestamp = messages[0].created_at
        user = messages[0].author
        text = '\n'.join([m.content for m in messages])
        if len(set([i.author.id for i in messages])) != 1:
            return await ctx.send("You can only quote one person at a time.")

        # Make sure they're not quoting themself
        if ctx.author.id in [i.author.id for i in messages]:
            return await ctx.send("You can't quote yourself :/")

        # Save to db
        quote_id = create_id()
        async with self.bot.database() as db:
            rows = await db(
                "SELECT * FROM user_quotes WHERE guild_id=$1 AND user_id=$2 AND timestamp=$3 AND text=$4",
                ctx.guild.id, user.id, timestamp, text
            )
            if rows:
                return await ctx.send(f"That message has already been quoted with quote ID `{rows[0]['quote_id']}`.")
            await db(
                "INSERT INTO user_quotes (quote_id, guild_id, user_id, text, timestamp) VALUES ($1, $2, $3, $4, $5)",
                quote_id, ctx.guild.id, user.id, text, timestamp
            )

        # Make embed
        with utils.Embed(use_random_colour=True) as embed:
            embed.set_author_to_user(user)
            embed.description = text
            embed.set_footer(text=f"Quote ID {quote_id.upper()}")
            embed.timestamp = timestamp

        # See if they have a quotes channel
        quote_channel_id = self.bot.guild_settings[ctx.guild.id].get('quote_channel_id')
        if quote_channel_id:
            channel = self.bot.get_channel(quote_channel_id) or await self.bot.fetch_channel(quote_channel_id)
            try:
                await channel.send(embed=embed)
            except (discord.Forbidden, AttributeError):
                pass

        # Output to user
        await ctx.send(f"Quote saved with ID `{quote_id.upper()}`", embed=embed)

    @quote.command(cls=utils.Command)
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def get(self, ctx:utils.Context, identifier):
        """Gets a quote from the database"""

        async with self.bot.database() as db:
            aliasRows = await db("SELECT * FROM quote_aliases WHERE alias=$1", identifier.lower())
            quoteRows = await db("SELECT * FROM user_quotes WHERE quote_id=$1", identifier.lower())
        if not aliasRows and not quoteRows:
            return await ctx.send(f"There's no quote with the identifier `{identifier.upper()}`.")
        if aliasRows and not quoteRows:
            quote_id = aliasRows[0]['quote_id']
            async with self.bot.database() as db:
                quoteRows = await db("SELECT * FROM user_quotes WHERE quote_id=$1", quote_id.lower())

        # Format into embed
        data = quoteRows[0]
        with utils.Embed(use_random_colour=True) as embed:
            user_id = data['user_id']
            user = self.bot.get_user(user_id)
            if user is None:
                embed.set_author(name=f"User ID {user_id}")
            else:
                embed.set_author_to_user(user)
            embed.description = data['text']
            embed.set_footer(text=f"Quote ID {quote_id.upper()}")
            embed.timestamp = data['timestamp']

        # Output to user
        return await ctx.send(embed=embed)

    @quote.command(cls=utils.Command)
    @commands.has_permissions(manage_guild=True)
    @commands.bot_has_permissions(send_messages=True)
    async def alias(self, ctx:utils.Context, quote_id:commands.clean_content, alias):
        """Adds an alias to a quote"""

        # Grab data from db
        async with self.bot.database() as db:
            rows = await db("SELECT * FROM user_quotes WHERE quote_id=$1", quote_id.lower())
        if not rows:
            return await ctx.send(f"There's no quote with the ID `{quote_id.upper()}`.")

        # Inserts data (alias) into db
        async with self.bot.database() as db:
            rows = await db("SELECT * FROM quote_aliases WHERE alias=$1", alias)
            if not rows: 
                await db("INSERT into quote_aliases VALUES($1, $2)", quote_id.lower(), alias.lower())
                await ctx.send(f"Added the alias {alias} to quote ID {quote_id.upper()}")
            else:
                await ctx.send("That alias is already being used.")


    @quote.command(cls=utils.Command)
    @commands.bot_has_permissions(send_messages=True)
    async def search(self, ctx:utils.Context, user:typing.Optional[discord.Member]=None, *, search_term:str=""):
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
        text_rows = []
        for row in rows:
            if len(row['text']) <= 50:
                text_rows.append(f"`{row['quote_id'].upper()}` - {row['text']}")
            else:
                text_rows.append(f"`{row['quote_id'].upper()}` - {row['text'][:100]}...")
        return await ctx.send('\n'.join(text_rows), allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False))

    @quote.command(cls=utils.Command)
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(send_messages=True)
    async def delete(self, ctx:utils.Context, *quote_ids:str):
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
