import discord
import voxelbotvbu as vbu


# class BotSettings(vbu.Cog):

#     @vbu.group()
#     @commands.has_permissions(manage_guild=True)
#     @commands.bot_has_permissions(send_messages=True, embed_links=True, add_reactions=True)
#     @commands.guild_only()
#     async def setup(self, ctx:vbu.Context):
#         """
#         Run the bot setup.
#         """

#         # Make sure it's only run as its own command, not a parent
#         if ctx.invoked_subcommand is not None:
#             return

#         # Create settings menu
#         settings_mention = vbu.SettingsMenuOption.get_guild_settings_mention
#         menu = vbu.SettingsMenu()
#         menu.add_multiple_options(
#             vbu.SettingsMenuOption(
#                 ctx=ctx,
#                 display=lambda c: "Set quote channel (currently {0})".format(settings_mention(c, 'quote_channel_id')),
#                 converter_args=(
#                     vbu.SettingsMenuConverter(
#                         prompt="What do you want to set the quote channel to?",
#                         asking_for="quote channel",
#                         converter=commands.TextChannelConverter,
#                     ),
#                 ),
#                 callback=vbu.SettingsMenuOption.get_set_guild_settings_callback('guild_settings', 'quote_channel_id'),
#             ),
#             vbu.SettingsMenuOption(
#                 ctx=ctx,
#                 display=lambda c: "Set reactions needed for quote (currently {0})".format(settings_mention(c, 'quote_reactions_needed')),
#                 converter_args=(
#                     vbu.SettingsMenuConverter(
#                         prompt="How many reactions should a message get to get quoted?",
#                         asking_for="reactions needed",
#                         converter=int,
#                     ),
#                 ),
#                 callback=vbu.SettingsMenuOption.get_set_guild_settings_callback('guild_settings', 'quote_reactions_needed'),
#             ),
#             vbu.SettingsMenuOption(
#                 ctx=ctx,
#                 display=lambda c: "Set automatic nickname fixer (currently {0})".format(c.bot.guild_settings[c.guild.id]['automatic_nickname_update']),
#                 converter_args=[("Do you want to enable automatic nickname fixing?", "auto nickname", vbu.converters.BooleanConverter)],
#                 callback=vbu.SettingsMenuOption.get_set_guild_settings_callback('guild_settings', 'automatic_nickname_update'),
#             ),
#             vbu.SettingsMenuOption(
#                 ctx=ctx,
#                 display=lambda c: "Set nickname change ban role (currently {0})".format(settings_mention(c, 'nickname_banned_role_id')),
#                 converter_args=(
#                     vbu.SettingsMenuConverter(
#                         prompt="Which role should be set to stop users changing their nickname?",
#                         asking_for="nickname change ban role",
#                         converter=commands.RoleConverter,
#                     ),
#                 ),
#                 callback=vbu.SettingsMenuOption.get_set_guild_settings_callback('guild_settings', 'nickname_banned_role_id'),
#             ),
#             vbu.SettingsMenuOption(
#                 ctx=ctx,
#                 display="Set up VC max members",
#                 callback=self.bot.get_command("setup vcmaxmembers"),
#             ),
#         )

#         # Run the menu
#         try:
#             await menu.start(ctx)
#             await ctx.send("Done setting up!")
#         except vbu.errors.InvokedMetaCommand:
#             pass

#     @setup.command()
#     @vbu.checks.meta_command()
#     async def vcmaxmembers(self, ctx:vbu.Context):
#         """
#         Run the bot setup.
#         """

#         menu = vbu.SettingsMenuIterable(
#             table_name='channel_list',
#             column_name='channel_id',
#             cache_key='max_vc_members',
#             database_key='MaxVCMembers',
#             key_display_function=lambda k: getattr(ctx.bot.get_channel(k), 'mention', 'none'),
#             converters=(
#                 vbu.SettingsMenuConverter(
#                     prompt="What voice channel do you want to set the max of?",
#                     asking_for="voice channel",
#                     converter=commands.VoiceChannelConverter,
#                 ),
#                 vbu.SettingsMenuConverter(
#                     prompt="How many members should be allowed in this VC?",
#                     asking_for="amount",
#                     converter=int,
#                 ),
#             ),
#         )
#         await menu.start(ctx)


settings_menu = vbu.menus.Menu(
    vbu.menus.Option(
        display=lambda ctx: f"Set quote channel (currently {ctx.get_mentionable_channel(ctx.bot.guild_settings[ctx.guild.id]['quote_channel_id']).mention})",
        component_display="Quote channel",
        converters=[
            vbu.menus.Converter(
                prompt="What channel do you want to set your quote channel to?",
                converter=discord.TextChannel,
            )
        ],
        allow_none=True,
        callback=vbu.menus.Menu.callbacks.set_table_column(vbu.menus.DataLocation.GUILD, "guild_settings", "quote_channel_id"),
        cache_callback=vbu.menus.Menu.callbacks.set_cache_from_key(vbu.menus.DataLocation.GUILD, "quote_channel_id"),
    ),
    vbu.menus.Option(
        display=lambda ctx: f"Set reactions needed for quote (currently {ctx.bot.guild_settings[ctx.guild.id]['quote_reactions_needed']})",
        component_display="Reactions needed",
        converters=[
            vbu.menus.Converter(
                prompt="How many reactions should a message need to get quoted?",
                converter=int,
            )
        ],
        allow_none=True,
        callback=vbu.menus.Menu.callbacks.set_table_column(vbu.menus.DataLocation.GUILD, "guild_settings", "quote_reactions_needed"),
        cache_callback=vbu.menus.Menu.callbacks.set_cache_from_key(vbu.menus.DataLocation.GUILD, "quote_reactions_needed"),
    ),
    vbu.menus.Option(
        display=lambda ctx: f"Set automatic nickname fixer (currently {ctx.bot.guild_settings[ctx.guild.id]['automatic_nickname_update']})",
        component_display="Reactions needed",
        converters=[
            vbu.menus.Converter(
                prompt="Do you want to enable automatic nickname fixing?",
                converter=bool,
            )
        ],
        allow_none=True,
        callback=vbu.menus.Menu.callbacks.set_table_column(vbu.menus.DataLocation.GUILD, "guild_settings", "automatic_nickname_update"),
        cache_callback=vbu.menus.Menu.callbacks.set_cache_from_key(vbu.menus.DataLocation.GUILD, "automatic_nickname_update"),
    ),
    vbu.menus.Option(
        display=lambda ctx: f"Set nickname change ban role (currently {ctx.get_mentionable_role(ctx.bot.guild_settings[ctx.guild.id]['nickname_banned_role_id']).mention})",
        component_display="Name change ban role",
        converters=[
            vbu.menus.Converter(
                prompt="Which role should be set to stop users changing their nickname?",
                converter=discord.Role,
            )
        ],
        allow_none=True,
        callback=vbu.menus.Menu.callbacks.set_table_column(vbu.menus.DataLocation.GUILD, "guild_settings", "nickname_banned_role_id"),
        cache_callback=vbu.menus.Menu.callbacks.set_cache_from_key(vbu.menus.DataLocation.GUILD, "nickname_banned_role_id"),
    ),
    vbu.menus.Option(
        display="VC max members",
        callback=vbu.menus.MenuIterable(
            select_sql="""SELECT * FROM channel_list WHERE guild_id=$1 AND key='MaxVCMembers'""",
            select_sql_args=lambda ctx: (ctx.guild.id,),
            insert_sql="""INSERT INTO channel_list (guild_id, channel_id, key, value) VALUES ($1, $2, 'MaxVCMembers', $3)""",
            insert_sql_args=lambda ctx, data: (ctx.guild.id, data[0].id, data[1],),
            delete_sql="""DELETE FROM channel_list WHERE guild_id=$1 AND channel_id=$2 AND key='MaxVCMembers'""",
            delete_sql_args=lambda ctx, row: (ctx.guild.id, row['channel_id'],),
            converters=[
                vbu.menus.Converter(
                    prompt="What channel would you like to blacklist users getting points in?",
                    converter=discord.VoiceChannel,
                ),
                vbu.menus.Converter(
                    prompt="What's the maximum number of unmuted people that should be allowed in that VC?",
                    converter=int,
                ),
            ],
            row_text_display=lambda ctx, row: ctx.get_mentionable_channel(row['channel_id']).name,
            row_component_display=lambda ctx, row: ctx.get_mentionable_channel(row['channel_id']).name,
            cache_callback=vbu.menus.Menu.callbacks.set_iterable_dict_cache(vbu.menus.DataLocation.GUILD, "max_vc_members"),
            cache_delete_callback=vbu.menus.Menu.callbacks.delete_iterable_dict_cache(vbu.menus.DataLocation.GUILD, "max_vc_members"),
            cache_delete_args=lambda row: (row['channel_id'],)
        ),
    ),
)


def setup(bot: vbu.Bot):
    x = settings_menu.get_cog(bot)
    bot.add_cog(x)
