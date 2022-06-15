import discord
from discord.ext import vbu

from .types.bot import Bot


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
        component_display="Automatic nickname fixer",
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
    # vbu.menus.Option(
    #     display="VC max members",
    #     callback=vbu.menus.MenuIterable(
    #         select_sql="""SELECT * FROM channel_list WHERE guild_id=$1 AND key='MaxVCMembers'""",
    #         select_sql_args=lambda ctx: (ctx.guild.id,),
    #         insert_sql="""INSERT INTO channel_list (guild_id, channel_id, key, value) VALUES ($1, $2, 'MaxVCMembers', $3)""",
    #         insert_sql_args=lambda ctx, data: (ctx.guild.id, data[0].id, data[1],),
    #         delete_sql="""DELETE FROM channel_list WHERE guild_id=$1 AND channel_id=$2 AND key='MaxVCMembers'""",
    #         delete_sql_args=lambda ctx, row: (ctx.guild.id, row['channel_id'],),
    #         converters=[
    #             vbu.menus.Converter(
    #                 prompt="What channel would you like to blacklist users getting points in?",
    #                 converter=discord.VoiceChannel,
    #             ),
    #             vbu.menus.Converter(
    #                 prompt="What's the maximum number of unmuted people that should be allowed in that VC?",
    #                 converter=int,
    #             ),
    #         ],
    #         row_text_display=lambda ctx, row: ctx.get_mentionable_channel(row['channel_id']).name,
    #         row_component_display=lambda ctx, row: ctx.get_mentionable_channel(row['channel_id']).name,
    #         cache_callback=vbu.menus.Menu.callbacks.set_iterable_dict_cache(vbu.menus.DataLocation.GUILD, "max_vc_members"),
    #         cache_delete_callback=vbu.menus.Menu.callbacks.delete_iterable_dict_cache(vbu.menus.DataLocation.GUILD, "max_vc_members"),
    #         cache_delete_args=lambda row: (row['channel_id'],)
    #     ),
    # ),
)


def setup(bot: Bot):
    bot.create_cog(settings_menu)

    
def teardown(bot: Bot):
    bot.remove_cog("Bot Settings")
