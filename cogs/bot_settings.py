from collections.abc import Callable, Awaitable

import discord
from discord.ext import vbu

from .types.bot import Bot


def _option_callback_with_dispatch(
    event: str, callback: Awaitable
) -> Callable[[vbu.SlashContext, list], Awaitable]:
    """An option callback that also dispatches an event when called."""

    async def wrapper(ctx: vbu.SlashContext, data: list):
        print(data)
        if data[0] is not None:
            ctx.bot.dispatch(event, data[0])
        return await callback(ctx, data)

    return wrapper


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
        display=lambda ctx: f"Set report channel (currently {ctx.get_mentionable_channel(ctx.bot.guild_settings[ctx.guild.id]['report_channel_id']).mention})",
        component_display="Report channel",
        converters=[
            vbu.menus.Converter(
                prompt="What channel do you want to send reports to?",
                converter=discord.TextChannel,
            )
        ],
        allow_none=True,
        callback=vbu.menus.Menu.callbacks.set_table_column(vbu.menus.DataLocation.GUILD, "guild_settings", "report_channel_id"),
        cache_callback=vbu.menus.Menu.callbacks.set_cache_from_key(vbu.menus.DataLocation.GUILD, "report_channel_id"),
    ),
    vbu.menus.Option(
        display=lambda ctx: f"Set staff role (currently {ctx.get_mentionable_role(ctx.bot.guild_settings[ctx.guild.id]['staff_role_id']).mention})",
        component_display="Staff role",
        converters=[
            vbu.menus.Converter(
                prompt="What role should be alerted for reports?",
                converter=discord.Role,
            )
        ],
        allow_none=True,
        callback=vbu.menus.Menu.callbacks.set_table_column(vbu.menus.DataLocation.GUILD, "guild_settings", "staff_role_id"),
        cache_callback=vbu.menus.Menu.callbacks.set_cache_from_key(vbu.menus.DataLocation.GUILD, "staff_role_id"),
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
    vbu.menus.Option(
        display=lambda ctx: f"Set custom role requirement (currently {ctx.get_mentionable_role(ctx.bot.guild_settings[ctx.guild.id]['custom_role_requirement_role_id']).mention})",
        component_display="Custom role requirement",
        converters=[
            vbu.menus.Converter(
                prompt="What role do you want to set as requirement for creating a custom role?",
                converter=discord.Role,
            )
        ],
        allow_none=True,
        callback=_option_callback_with_dispatch(
            "custom_role_requirement_update",
            vbu.menus.Menu.callbacks.set_table_column(
                vbu.menus.DataLocation.GUILD,
                "guild_settings",
                "custom_role_requirement_role_id",
            ),
        ),
        cache_callback=vbu.menus.Menu.callbacks.set_cache_from_key(
            vbu.menus.DataLocation.GUILD, "custom_role_requirement_role_id"
        ),
    ),
    vbu.menus.Option(
        display=lambda ctx: f"Set custom role parent (all custom roles will be right beneath this one. Currently {ctx.get_mentionable_role(ctx.bot.guild_settings[ctx.guild.id]['custom_role_parent_role_id']).mention})",
        component_display="Custom role parent",
        converters=[
            vbu.menus.Converter(
                prompt="Under what role should the custom roles be positioned?\n> **WARNING:** This will lag out the server for a bit.",
                converter=discord.Role,
            )
        ],
        allow_none=True,
        callback=_option_callback_with_dispatch(
            "custom_role_parent_update",
            vbu.menus.Menu.callbacks.set_table_column(
                vbu.menus.DataLocation.GUILD,
                "guild_settings",
                "custom_role_parent_role_id",
            ),
        ),
        cache_callback=vbu.menus.Menu.callbacks.set_cache_from_key(
            vbu.menus.DataLocation.GUILD, "custom_role_parent_role_id"
        ),
    ),
)


def setup(bot: Bot):
    x = settings_menu.create_cog(bot)
    bot.add_cog(x)


def teardown(bot: Bot):
    bot.remove_cog("Bot Settings")
