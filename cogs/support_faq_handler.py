from datetime import datetime as dt, timedelta

import discord
from discord.ext import commands, tasks
import voxelbotutils as utils


SOCIAL_GUILD_ID = 208895639164026880
SOCIAL_SUPPORT_CHANNEL_ID = 689189589776203861
SUPPORT_GUILD_ID = 830286019520626710
BOT_PICKER_CHANNEL_ID = 830286547247955998
PICKABLE_FAQ_CHANNELS = {
    "<:marriage_bot:643484716607209482>": 830294468929912842,  # MarriageBot Support
    "<:flower:777636276790624256>": 830294484045529140,  # Flower Support
    "<:big_ben:709600097574584420>": 830294528958398464,  # Big Ben Support
    "\N{BLACK QUESTION MARK ORNAMENT}": 830546400542589019,  # Other Support
    "\N{SPEECH BALLOON}": 830546422930604072,  # Hang out
}
FAQ_MESSAGES = {
    "830294468929912842": [
        "None of the commands are working",
        "I can't disown my child",
        "Can you copy my MarriageBot family into Gold?",
    ],
    "830294484045529140": [
        "None of the commands are working",
        "I can't water my plant",
        "What's the best plant?",
        "How do I give pots to people?",
    ],
    "830294528958398464": [
        "None of the commands are working",
        "How do I set it up?",
        "It isn't giving out the role",
    ],
}


class SupportFAQHandler(utils.Cog):

    BOT_PICKER_MESSAGE_ID = None

    def __init__(self, bot:utils.Bot):
        super().__init__(bot)
        self.guild_purge_loop.start()
        self.faq_webhook = discord.Webhook.from_url(
            bot.config['command_data']['faq_webhook'],
            adapter=discord.AsyncWebhookAdapter(bot.session),
        )
        self.faq_webhook._state = bot._connection
        self.member_join_waits = {}
        self.message_cache = {}

    def cog_unload(self):
        self.guild_purge_loop.cancel()

    @tasks.loop(hours=6)
    async def guild_purge_loop(self):
        """
        Automatically purges the support guild.
        """

        await self.bot.get_guild(SUPPORT_GUILD_ID).prune_members(days=7, compute_prune_count=False, reason="Automatic purge event.")

    @guild_purge_loop.before_loop
    async def before_guild_purge_loop(self):
        return await self.bot.wait_until_ready()

    def send_faq_log(self, member:discord.User, content:str, *args, **kwargs) -> None:
        """
        Sends a message using the webhook.
        """

        async def wrapper():
            try:
                current_message, last_update, current_text = self.message_cache.get(member.id)
            except Exception:
                current_message = None
            if current_message and (dt.utcnow() - last_update) < timedelta(minutes=5):
                new_text = current_text + "\n" + content
                await current_message.edit(content=new_text)
            else:
                new_text = content
                current_message = await self.faq_webhook.send(content, *args, wait=True, **kwargs)
            self.message_cache[member.id] = (current_message, dt.utcnow(), new_text)
        self.bot.loop.create_task(wrapper())

    def ghost_ping(self, channel:discord.TextChannel, user:discord.User) -> None:
        """
        Sends and deletes a user ping to the given channel
        """

        async def wrapper():
            m = await channel.send(user.mention)
            await m.delete()
        self.bot.loop.create_task(wrapper())

    def wait_for_join(self, member:discord.User) -> None:
        """
        Waits for a member to join the VFL social server, then sends a webhook to the log channel.
        """

        async def wrapper():
            try:
                await self.bot.wait_for("member_join", check=lambda m: m.id == member.id and m.guild.id == SOCIAL_GUILD_ID, timeout=60)
            except asyncio.TimeoutError:
                self.send_faq_log(member, f"{member.mention} (`{member.id}`) did not join the main VFL server.")
                return
            except asyncio.CancelledError:
                return
            else:
                self.send_faq_log(member, f"{member.mention} (`{member.id}`) joined the main VFL server.")
            try:
                await self.bot.wait_for("message", check=lambda m: m.author.id == member.id and m.channel.id == SOCIAL_SUPPORT_CHANNEL_ID, timeout=120)
            except asyncio.TimeoutError:
                self.send_faq_log(member, f"{member.mention} (`{member.id}`) did not send a message in the main VFL's support channel.")
                return
            except asyncio.CancelledError:
                return
            else:
                self.send_faq_log(member, f"{member.mention} (`{member.id}`) sent their question in the main VFL's support channel.")
        task = self.bot.loop.create_task(wrapper())
        current_task = self.member_join_waits.get(member.id)
        if current_task:
            current_task.cancel()
        self.member_join_waits[member.id] = task

    @utils.Cog.listener()
    async def on_member_join(self, member:discord.Member):
        """
        Ping a webhook when a member joins the guild.
        """

        if member.guild.id != SUPPORT_GUILD_ID:
            return
        self.send_faq_log(member, f"{member.mention} (`{member.id}`) has joined the server.")

    @utils.Cog.listener()
    async def on_member_remove(self, member:discord.Member):
        """
        Ping a webhook when a member joins the guild.
        """

        if member.guild.id != SUPPORT_GUILD_ID:
            return
        self.send_faq_log(member, f"{member.mention} (`{member.id}`) has left the server.")
        self.message_cache[member.id] = (None, None)

    @utils.Cog.listener()
    async def on_raw_reaction_add(self, payload:discord.RawReactionActionEvent):
        """
        Runs the support guild reaction handler.
        """

        # Make sure the guild is right
        if payload.guild_id != SUPPORT_GUILD_ID:
            return
        guild = self.bot.get_guild(SUPPORT_GUILD_ID)
        member = guild.get_member(payload.user_id)
        if member.bot:
            return

        # See if we're looking at the bot picker
        if payload.channel_id == BOT_PICKER_CHANNEL_ID:
            new_channel_id = PICKABLE_FAQ_CHANNELS[str(payload.emoji)]
            new_channel = self.bot.get_channel(new_channel_id)
            await new_channel.set_permissions(member, read_messages=True)
            self.send_faq_log(member, f"{member.mention} (`{member.id}`) has been given access to **{new_channel.category.name}**.")
            self.ghost_ping(new_channel, member)
            return

        # We could be looking at an faq channel
        current_channel = self.bot.get_channel(payload.channel_id)
        if current_channel.name == "faqs":
            current_category = current_channel.category
            try:
                emoji_number = int(str(payload.emoji)[0])
                new_channel = current_category.channels[emoji_number]  # They gave a number
                self.send_faq_log(member, f"{member.mention} (`{member.id}`) in {current_category.name} is looking at FAQ **{FAQ_MESSAGES[str(current_channel.id)][emoji_number - 1]}**.")
            except ValueError:
                new_channel_id = PICKABLE_FAQ_CHANNELS["\N{BLACK QUESTION MARK ORNAMENT}"]  # Take them to other support
                new_channel = self.bot.get_channel(new_channel_id)
                self.send_faq_log(member, f"{member.mention} (`{member.id}`) in {current_category.name} has a question not in the FAQ.")
            await new_channel.set_permissions(member, read_messages=True)
            self.ghost_ping(new_channel, member)
            return

        # It's probably a tick mark
        if str(payload.emoji) == "\N{HEAVY CHECK MARK}":
            self.send_faq_log(member, f"{member.mention} (`{member.id}`) gave a tick mark in **{current_channel.mention}**.")

    @utils.command()
    @commands.is_owner()
    async def setupsupportguild(self, ctx:utils.Context):
        """
        Sends some sexy new messages into the support guild.
        """

        # Make sure we're in the right guild
        if ctx.guild is None or ctx.guild.id != SUPPORT_GUILD_ID:
            return await ctx.send("This can only be run on the set support guild.")

        # This could take a while
        async with ctx.typing():

            # Remake the FAQ channel for each channel
            for channel_id_str, embed_lines in FAQ_MESSAGES.items():

                # Get the category object
                channel = self.bot.get_channel(int(channel_id_str))
                category = channel.category

                # Get the faq channel and delete the old message
                faq_channel = category.channels[0]
                if faq_channel.name != "faqs":
                    return await ctx.send(
                        f"The first channel in the **{category_name}** category isn't called **faqs**.",
                        allowed_mentions=discord.AllowedMentions.none(),
                    )

                # Make the embed
                emoji_lines = [f"{index}\N{COMBINING ENCLOSING KEYCAP} **{string}**" for index, string in enumerate(embed_lines, start=1)]
                description = "\n".join(emoji_lines + ["\N{BLACK QUESTION MARK ORNAMENT} **Other**"])
                new_embed = utils.Embed(title="What issue are you having?", description=description, colour=0x1)

                # See if it's anything new
                current_messages = await faq_channel.history(limit=1).flatten()
                if current_messages and current_messages[0].embeds and current_messages[0].embeds[0].to_dict() == new_embed.to_dict():
                    continue
                await current_messages[0].delete()
                new_message = await faq_channel.send(embed=new_embed)
                for emoji, item in [i.strip().split(" ", 1) for i in new_message.embeds[0].description.strip().split("\n")]:
                    await new_message.add_reaction(emoji)

        # And we should be done at this point
        await ctx.okay()


def setup(bot:utils.Bot):
    x = SupportFAQHandler(bot)
    bot.add_cog(x)
