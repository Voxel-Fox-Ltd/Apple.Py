from discord.ext import commands, vbu
import discord

class ReportCommand(vbu.Cog):

    @commands.command(
        application_command_meta=commands.ApplicationCommandMeta()
    )
    # Perhaps giving users a way to infinitely ping staff isn't the best idea...
    # ...but they could also be legitimate reports
    @commands.cooldown(1, 5, commands.BucketType.channel)
    @commands.guild_only()
    async def report(self, ctx: vbu.Context, reported: discord.Member, reason: str = "*no reason provided*"):
        """
        Sends a report to the assigned reports channel.
        """

        # If they reported themselves
        if ctx.author.id == reported.id:
            return await ctx.send("It doesn't make sense to report yourself...")

        # Get the report channel
        report_channel_id = self.bot.guild_settings[ctx.guild.id]['report_channel_id']
        
        # If an ID is not even set
        if not report_channel_id: 
            return await ctx.send("A report channel was not chosen in the settings. Run the `/settings` command to set a channel.")

        # Get the channel object
        report_channel: discord.TextChannel = ctx.guild.get_channel(report_channel_id)

        # Reports channel must be valid
        if not report_channel:
            try: # Fetch the channel if we can't find it
                report_channel = await ctx.guild.fetch_channel(report_channel_id)
            except discord.NotFound: # The channel doesn't exist 
                return await ctx.send("The report channel ID does not point to a channel in this server.")
            except Exception: # Something else went wrong
                return await ctx.send("Something went wrong finding the report channel. Run the `/settings` command to set a valid channel.")

        # Get the staff role
        staff_role_id = self.bot.guild_settings[ctx.guild.id]["staff_role_id"]
        staff_role: discord.Role = ctx.guild.get_role(staff_role_id)
        
        # Try to find a staff role if we haven't already
        if not staff_role:
            try: # Fetch the role if we can't find it
                staff_role = await ctx.guild.fetch_role(staff_role_id)
            except Exception:
                # We tried our best, we just won't ping a role
                pass

        # Create a message with the reporter, who they're reporting, the reason, and the message link
        # In embed form
        embed = vbu.Embed(colour=0xFF0000)

        # All the necessary information - we cut off the reason to the first 500 characters 
        embed.description = f"""
                            **Reported:** {reported.mention} (ID: {reported.id})
                            **Reason:** {reason[:500]}
                            **Channel:** {ctx.message.channel.mention} ([Link](<{ctx.message.jump_url}>))
                            """
        
        # Make the embed asthetic if we can (add an author and an image of the reported person's avatar)
        try:
            embed.set_author_to_user(ctx.author)
            embed.set_thumbnail(reported.avatar.url)
        except:
            # Probably a problem with the image
            pass
        
        # Send the message to the reports channel
        await report_channel.send(
            content =
                f"__{staff_role.mention if staff_role else ''} New report from {ctx.author.mention} against {reported.mention}__",
                embed=embed,
            allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=True)
            )

        # If you want it to just be a message (no embed)
        # await report_channel.send(
        #     content = f"{staff_role.mention if staff_role else ''} New report from {ctx.author.mention} against {reported.mention}.\n" +
        #               f"**Reported:** {reported.mention} (ID: {reported.id})\n" + 
        #               f"**Reason:** {reason[:500]}\n" + 
        #               f"**Channel:** {ctx.message.channel.mention} (<{ctx.message.jump_url}>)",
        #     allowed_mentions = discord.AllowedMentions(everyone=False, users=False, roles=True)
        # )

        # Acknowledge the original command message
        await ctx.okay()


def setup(bot: vbu.Bot):
    x = ReportCommand(bot)
    bot.add_cog(x)
