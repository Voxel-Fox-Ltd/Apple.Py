from discord.ext import commands
import voxelbotutils as utils


class BotSettings(utils.Cog):

    @utils.group()
    @commands.has_permissions(manage_guild=True)
    @commands.bot_has_permissions(send_messages=True, embed_links=True, add_reactions=True)
    @commands.guild_only()
    async def setup(self, ctx:utils.Context):
        """
        Run the bot setup.
        """

        # Make sure it's only run as its own command, not a parent
        if ctx.invoked_subcommand is not None:
            return

        # Create settings menu
        menu = utils.SettingsMenu()
        settings_mention = utils.SettingsMenuOption.get_guild_settings_mention
        menu.bulk_add_options(
            ctx,
            {
                'display': lambda c: "Set quote channel (currently {0})".format(settings_mention(c, 'quote_channel_id')),
                'converter_args': [("What do you want to set the quote channel to?", "quote channel", commands.TextChannelConverter)],
                'callback': utils.SettingsMenuOption.get_set_guild_settings_callback('guild_settings', 'quote_channel_id'),
            },
            {
                'display': lambda c: "Set reactions needed for quote (currently {0})".format(settings_mention(c, 'quote_reactions_needed')),
                'converter_args': [("How many reactions should a message get to get quoted?", "reactions needed", int)],
                'callback': utils.SettingsMenuOption.get_set_guild_settings_callback('guild_settings', 'quote_reactions_needed'),
            },
            {
                'display': lambda c: "Set automatic nickname fixer (currently {0})".format(c.bot.guild_settings[c.guild.id]['automatic_nickname_update']),
                'converter_args': [("Do you want to enable automatic nickname fixing?", "auto nickname", utils.converters.BooleanConverter)],
                'callback': utils.SettingsMenuOption.get_set_guild_settings_callback('guild_settings', 'automatic_nickname_update'),
            },
            {
                'display': lambda c: "Set nickname change ban role (currently {0})".format(settings_mention(c, 'nickname_banned_role_id')),
                'converter_args': [("Which role should be set to stop users changing their nickname?", "nickname change ban role", commands.RoleConverter)],
                'callback': utils.SettingsMenuOption.get_set_guild_settings_callback('guild_settings', 'nickname_banned_role_id'),
            },
            {
                'display': "Set up VC max members",
                'callback': self.bot.get_command("setup vcmaxmembers"),
            },
        )
        try:
            await menu.start(ctx)
            await ctx.send("Done setting up!")
        except utils.errors.InvokedMetaCommand:
            pass

    @setup.command()
    @utils.checks.meta_command()
    async def vcmaxmembers(self, ctx:utils.Context):
        """
        Run the bot setup.
        """

        # Create settings menu
        key_display_function = lambda k: getattr(ctx.bot.get_channel(k), 'mention', 'none')
        menu = utils.SettingsMenuIterable(
            'channel_list', 'channel_id', 'max_vc_members', 'MaxVCMembers',
            commands.VoiceChannelConverter, "What voice channel do you want to set the max of?", key_display_function,
            int, "How many members should be allowed in this VC?"
        )
        await menu.start(ctx)

    @utils.group(enabled=False)
    @commands.bot_has_permissions(send_messages=True, embed_links=True, add_reactions=True)
    @utils.cooldown.cooldown(1, 60, commands.BucketType.member)
    @commands.guild_only()
    async def usersettings(self, ctx:utils.Context):
        """
        Run the bot setup.
        """

        # Make sure it's only run as its own command, not a parent
        if ctx.invoked_subcommand is not None:
            return

        # Create settings menu
        menu = utils.SettingsMenu()
        settings_mention = utils.SettingsMenuOption.get_user_settings_mention
        menu.bulk_add_options(
            ctx,
            {
                'display': lambda c: "Set setting (currently {0})".format(settings_mention(c, 'setting_id')),
                'converter_args': [("What do you want to set the setting to?", "setting channel", commands.TextChannelConverter)],
                'callback': utils.SettingsMenuOption.get_set_user_settings_callback('user_settings', 'setting_id'),
            },
        )
        try:
            await menu.start(ctx)
            await ctx.send("Done setting up!")
        except utils.errors.InvokedMetaCommand:
            pass


def setup(bot:utils.Bot):
    x = BotSettings(bot)
    bot.add_cog(x)
