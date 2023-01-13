from io import BytesIO

import discord
from discord.ext import commands, vbu


class StickerStealer(vbu.Cog):

    @commands.context_command(name="Steal This Sticker")
    async def _context_command_steal_sticker(
            self,
            ctx: vbu.SlashContext,
            message: discord.Message):

        await commands.has_permissions(manage_guild=True).predicate(ctx)
        await commands.guild_only().predicate(ctx)

        if message.stickers and len(message.stickers) > 0:
            pass
        else:
            return await ctx.send(
                "This message does not have a sticker.",
                ephemeral=True,
            )

        sticker = message.stickers[0]
        try:
            new_sticker = await ctx.guild.create_sticker(
                name=sticker.name,
                description=sticker.name,
                emoji="::",
                file=discord.File(BytesIO(await sticker.read())),
            )
        except (discord.Forbidden, discord.HTTPException) as e:
            return await ctx.send(
                f"Failed to create the sticker due to: {e}",
                ephemeral=True
            )
        else:
            await ctx.send(f"Successfully created the sticker: {new_sticker.name}.")


def setup(bot: vbu.Bot):
    x = StickerStealer(bot)
    bot.add_cog(x)
