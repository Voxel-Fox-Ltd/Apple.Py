import string
import random
import re
import asyncio
import typing

import discord
from discord.ext import commands, vbu


def create_id(n: int = 5):
    """
    Generates a generic 5 character-string to use as an ID.
    """

    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=n)).lower()


class QuoteCommands(vbu.Cog):

    IMAGE_URL_REGEX = re.compile(r"(http(?:s?):)([/|.|\w|\s|-])*\.(?:jpg|gif|png|jpeg|webp)")
    QUOTE_SEARCH_CHARACTER_CUTOFF = 100

    async def get_quote_messages(
            self, ctx: vbu.Context, messages: typing.List[discord.Message], *,
            allow_self_quote: bool = False) -> dict:
        """
        Gets the messages that the user has quoted, returning a dict with keys `success` (bool) and `message` (str or voxelbotutils.Embed).
        If `success` is `False`, then the resulting `message` can be directly output to the user, and if it's `True` then we can go ahead
        with the message save flowthrough.
        """

        # Make sure they have a quote channel
        assert ctx.guild
        if self.bot.guild_settings[ctx.guild.id].get('quote_channel_id') is None:
            func = "You don't have a quote channel set!"
            return {'success': False, 'message': func}

        # Make sure a message was passed
        if not messages:
            if ctx.message.reference is not None:
                message_from_reply = await ctx.fetch_message(ctx.message.reference.message_id)
                messages = [message_from_reply]
            else:
                return {'success': False, 'message': "I couldn't find any references to messages in your command call."}

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
                return {'success': False, 'message': "Those messages are too far apart to quote together."}
            if not i.content or i.attachments:
                if len(i.attachments) == 0:
                    return {'success': False, 'message': "Embeds can't be quoted."}
                if i.attachments:
                    return {'success': False, 'message': "You can't quote multiple messages when quoting images."}

        # Validate the message content
        for message in messages:
            if (quote_is_url and message.content) or (message.content and message.attachments and message.content != message.attachments[0].url):
                return {'success': False, 'message': "You can't quote both messages and images."}
            elif message.embeds and getattr(message.embeds[0].thumbnail, "url", None) != message.content:
                return {'success': False, 'message': "You can't quote embeds."}
            elif len(message.attachments) > 1:
                return {'success': False, 'message': "Multiple images can't be quoted."}
            elif message.attachments:
                if self.IMAGE_URL_REGEX.search(message.attachments[0].url) is None:
                    return {'success': False, 'message': "The attachment in that image isn't a valid image URL."}
                message.content = message.attachments[0].url
                quote_is_url = True

        # Validate input
        timestamp = discord.utils.naive_dt(messages[0].created_at)
        user = messages[0].author
        text = '\n'.join([m.content for m in messages])
        if len(set([i.author.id for i in messages])) != 1:
            return {'success': False, 'message': "You can only quote one person at a time."}

        # Make sure they're not quoting themself if there are no reactions needed
        message_author = messages[0].author
        reactions_needed = self.bot.guild_settings[ctx.guild.id]['quote_reactions_needed']
        if ctx.author.id in self.bot.owner_ids:
            pass
        elif ctx.author.id == message_author.id and (reactions_needed or allow_self_quote is False):
            return {'success': False, 'message': "You can't quote yourself when there's no vote :/"}

        # Return an embed
        with vbu.Embed(use_random_colour=True) as embed:
            embed.set_author_to_user(user)
            if quote_is_url:
                embed.set_image(text)
            else:
                embed.description = text
            embed.timestamp = timestamp
        return {'success': True, 'message': embed, 'user': user, 'timestamp': timestamp}

    @commands.group(
        invoke_without_command=True,
        application_command_meta=commands.ApplicationCommandMeta(),
    )
    @commands.bot_has_permissions(send_messages=True, embed_links=True, add_reactions=True)
    @commands.guild_only()
    async def quote(self, ctx: vbu.Context, messages: commands.Greedy[discord.Message]):
        """
        Quotes a user's message to the guild's quote channel.
        """

        # Make sure no subcommand is passed
        if ctx.invoked_subcommand is not None:
            return
        response = await self.get_quote_messages(ctx, messages)

        # Make embed
        if response['success'] is False:
            return await ctx.send(response['message'])
        embed = response['message']
        user = response['user']
        timestamp = response['timestamp']

        # See if we should bother saving it
        reactions_needed = self.bot.guild_settings[ctx.guild.id]['quote_reactions_needed']
        ask_to_save_message = await ctx.send(
            f"Should I save this quote? If I receive {reactions_needed} positive reactions in the next 60 seconds, the quote will be saved.",
            embed=embed,
        )
        self.bot.loop.create_task(ask_to_save_message.add_reaction("\N{THUMBS UP SIGN}"))
        self.bot.loop.create_task(ask_to_save_message.add_reaction("\N{THUMBS DOWN SIGN}"))
        await asyncio.sleep(60)

        # Get the message again so we can refresh the reactions
        try:
            ask_to_save_message_again = await ask_to_save_message.channel.fetch_message(ask_to_save_message.id)
            reaction_count = sum([i.count if str(i.emoji) == "\N{THUMBS UP SIGN}" else -i.count if str(i.emoji) == "\N{THUMBS DOWN SIGN}" else 0 for i in ask_to_save_message_again.reactions])
        except discord.HTTPException:
            return
        try:
            await ask_to_save_message.delete()
        except discord.HTTPException:
            pass
        if reaction_count < reactions_needed:
            return await ctx.send(f"_Not_ saving the quote asked by {ctx.author.mention} - not enough reactions received.")

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

        # And save it to the database
        async with vbu.Database() as db:
            await db(
                """INSERT INTO user_quotes (quote_id, guild_id, channel_id, message_id, user_id, timestamp, quoter_id)
                VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                quote_id, ctx.guild.id, posted_message.channel.id, posted_message.id, user.id, timestamp, ctx.author.id,
            )

        # Output to user
        await ctx.send(f"{ctx.author.mention}'s quote request saved with ID `{quote_id.upper()}`", embed=embed)

    @commands.context_command(name="Quote message")
    async def _context_command_quote_create(self, ctx: vbu.Context, message: discord.Message):
        command = self.quote_create
        await command.can_run(ctx)
        await ctx.invoke(command, message)

    @quote.command(name="create")
    @commands.bot_has_permissions(send_messages=True, embed_links=True, add_reactions=True)
    @commands.guild_only()
    async def quote_create(self, ctx: vbu.Context, message: discord.Message):
        """
        Quotes a user's message to the guild's quote channel.
        """

        await self.quote(ctx, [message])

    @quote.command(name="force")
    @commands.has_guild_permissions(manage_guild=True)
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def quote_force(self, ctx: vbu.Context, messages: commands.Greedy[discord.Message]):
        """
        Quotes a user's message to the guild's quote channel.
        """

        # Make sure no subcommand is passed
        if ctx.invoked_subcommand is not None:
            return
        response = await self.get_quote_messages(ctx, messages, allow_self_quote=True)

        # Make embed
        if response['success'] is False:
            return await ctx.send(response['message'])
        embed = response['message']
        user = response['user']
        timestamp = response['timestamp']

        # See if they have a quotes channel
        quote_channel_id = self.bot.guild_settings[ctx.guild.id].get('quote_channel_id')
        quote_id = create_id()
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

        # And save it to the database
        async with vbu.Database() as db:
            await db(
                """INSERT INTO user_quotes (quote_id, guild_id, channel_id,
                message_id, user_id, timestamp, quoter_id)
                VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                quote_id, ctx.guild.id, posted_message.channel.id,
                posted_message.id, user.id, timestamp.replace(tzinfo=None), ctx.author.id,
            )

        # Output to user
        await ctx.send(f"{ctx.author.mention}'s quote saved with ID `{quote_id.upper()}`", embed=embed)

    @quote.command(
        name="get",
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="identifier",
                    description="The ID of the quote that you want to get.",
                    type=discord.ApplicationCommandOptionType.string,
                ),
            ],
        ),
    )
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def quote_get(self, ctx: vbu.Context, identifier: str):
        """
        Gets a quote from the guild's quote channel.
        """

        # Get quote from database
        async with vbu.Database() as db:
            quote_rows = await db(
                """SELECT user_quotes.quote_id as quote_id, user_id, channel_id, message_id FROM user_quotes LEFT JOIN
                quote_aliases ON user_quotes.quote_id=quote_aliases.quote_id
                WHERE user_quotes.quote_id=$1 OR quote_aliases.alias=$1""",
                identifier.lower(),
            )
        if not quote_rows:
            return await ctx.send(
                f"There's no quote with the identifier `{identifier.upper()}`.",
                allowed_mentions=discord.AllowedMentions.none(),
            )

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

        # try to refresh the user name and icon of the embed by getting the user from the user ID in the DB
        quote_embed = message.embeds[0]
        quote_author = self.bot.get_user(data['user_id'])
        if quote_author:
            quote_embed.set_author(name=quote_author.display_name, icon_url=quote_author.display_avatar.url)

        # Output to user
        return await ctx.send(embed=quote_embed)

    @quote.command(
        name="random",
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="user",
                    description="The user whose quotes you want to search.",
                    type=discord.ApplicationCommandOptionType.user,
                    required=False,
                ),
            ],
        ),
    )
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    async def quote_random(self, ctx: vbu.Context, user: discord.Member = None):
        """
        Gets a random quote for a given user.
        """

        # Get quote from database
        user = user or ctx.author
        async with vbu.Database() as db:
            quote_rows = await db(
                """SELECT quote_id as quote_id, user_id, channel_id, message_id
                FROM user_quotes WHERE user_id=$1 AND guild_id=$2 ORDER BY RANDOM() LIMIT 1""",
                user.id, ctx.guild.id,
            )
        if not quote_rows:
            return await ctx.send(f"{user.mention} has no available quotes.", allowed_mentions=discord.AllowedMentions.none())

        # Get the message
        data = quote_rows[0]
        if data['channel_id'] is None:
            self.logger.info(f"Deleting legacy quote - {data['quote_id']}")
            async with vbu.Database() as db:
                await db("DELETE FROM user_quotes WHERE quote_id=$1", data['quote_id'])
            return await ctx.reinvoke()
        channel = self.bot.get_channel(data['channel_id'])
        if channel is None:
            self.logger.info(f"Deleting quote from deleted channel - {data['quote_id']}")
            async with vbu.Database() as db:
                await db("DELETE FROM user_quotes WHERE quote_id=$1", data['quote_id'])
            return await ctx.reinvoke()
        try:
            message = await channel.fetch_message(data['message_id'])
            assert message is not None
        except (AssertionError, discord.HTTPException):
            self.logger.info(f"Deleting quote from deleted message - {data['quote_id']}")
            async with vbu.Database() as db:
                await db("DELETE FROM user_quotes WHERE quote_id=$1", data['quote_id'])
            return await ctx.reinvoke()

        # Output to user
        quote_embed = message.embeds[0]
        quote_author = self.bot.get_user(data['user_id'])
        if quote_author:
            quote_embed.set_author(name=quote_author.display_name, icon_url=quote_author.display_avatar.url)
        return await ctx.send(embed=quote_embed)

    # @quote.group(name="alias", invoke_without_command=True)
    # @commands.guild_only()
    # @commands.has_guild_permissions(manage_guild=True)
    # @commands.bot_has_permissions(send_messages=True)
    # async def quote_alias(self, ctx: vbu.Context, quote_id: commands.clean_content, alias: commands.clean_content):
    #     """
    #     Adds an alias to a quote.
    #     """

    #     # Grab data from db
    #     async with vbu.Database() as db:
    #         rows = await db("SELECT * FROM user_quotes WHERE quote_id=$1 AND guild_id=$2", quote_id.lower(), ctx.guild.id)
    #     if not rows:
    #         return await ctx.send(f"There's no quote with the ID `{quote_id.upper()}`.")

    #     # Insert alias into db
    #     async with vbu.Database() as db:
    #         rows = await db("SELECT * FROM quote_aliases WHERE alias=$1", alias)
    #         if rows:
    #             return await ctx.send(f"The alias `{alias}` is already being used.")
    #         await db("INSERT INTO quote_aliases (quote_id, alias) VALUES ($1, $2)", quote_id.lower(), alias.lower())
    #     await ctx.send(f"Added the alias `{alias.upper()}` to quote ID `{quote_id.upper()}`.")

    # @quote.command(name="list")
    # @commands.guild_only()
    # @commands.has_guild_permissions(manage_guild=True)
    # @commands.bot_has_permissions(send_messages=True)
    # async def quote_list(self, ctx: vbu.Context, user: discord.Member=None):
    #     """
    #     List the IDs of quotes for a user.
    #     """

    #     # Grab data from db
    #     user = user or ctx.author
    #     async with vbu.Database() as db:
    #         rows = await db("SELECT quote_id FROM user_quotes WHERE user_id=$1 AND guild_id=$2", user, ctx.guild.id)
    #     if not rows:
    #         embed = vbu.Embed(
    #             use_random_colour=True, description="This user has no quotes.",
    #         ).set_author_to_user(user)
    #         return await ctx.send(embed=embed)
    #     embed = vbu.Embed(
    #         use_random_colour=True, description="\n".join([i['quote_id'] for i in rows[:50]]),
    #     ).set_author_to_user(user)
    #     return await ctx.send(embed=embed)

    # @quote_alias.command(name="remove", aliases=["delete"])
    # @commands.guild_only()
    # @commands.has_guild_permissions(manage_guild=True)
    # @commands.bot_has_permissions(send_messages=True)
    # async def quote_alias_remove(self, ctx: vbu.Context, alias: commands.clean_content):
    #     """
    #     Deletes an alias from a quote.
    #     """

    #     # Grab data from db
    #     async with vbu.Database() as db:
    #         quote_rows = await db(
    #             """SELECT user_quotes.quote_id as quote_id, user_id, channel_id, message_id FROM user_quotes LEFT JOIN
    #             quote_aliases ON user_quotes.quote_id=quote_aliases.quote_id
    #             WHERE quote_aliases.alias=$1 AND guild_id=$2""",
    #             alias.lower(), ctx.guild.id
    #         )
    #         if not quote_rows:
    #             return await ctx.send(f"There's no quote with the alias `{alias.upper()}`.")
    #         await db("DELETE FROM quote_aliases WHERE alias=$1", alias.lower())
    #     return await ctx.send(f"Deleted alias `{alias.upper()}`.")

    @quote.command(
        name="delete",
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="quote_id",
                    description="The ID of the quote that you want to delete.",
                    type=discord.ApplicationCommandOptionType.string,
                ),
            ],
        ),
    )
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(send_messages=True)
    async def quote_delete(self, ctx: vbu.Context, quote_id: str):
        """
        Deletes a quote from your server.
        """

        # quote_ids = [i.lower() for i in quote_ids]
        quote_ids = [quote_id.lower()]
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

        async with vbu.Database() as db:
            await db("DELETE FROM user_quotes WHERE quote_id=ANY($1) AND guild_id=$2", quote_ids, ctx.guild.id)
        return await ctx.send("Deleted quote(s).")


def setup(bot: vbu.Bot):
    x = QuoteCommands(bot)
    bot.add_cog(x)
