from io import BytesIO

import discord
from discord.ext import commands, vbu


class StickerStealer(vbu.Cog):

    @commands.context_command(name="Steal This Sticker")
    async def _context_command_steal_sticker(self, ctx: vbu.SlashContext, message: discord.Message):
        command = self.steal_sticker
        await command.can_run(ctx)
        await ctx.invoke(command, message)

    @commands.command(name="stealsticker")
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def steal_sticker(self, ctx: vbu.Context, message: discord.Message):
        """
        Steal a sticker and add to the current server.
        """

        assert ctx.guild
        if message.stickers and len(message.stickers) > 0:
            sticker = message.stickers[0]
            try:
                await ctx.guild.create_sticker(
                    name=sticker.name,
                    description=sticker.name,
                    emoji="::",
                    file=discord.File(BytesIO(await sticker.read())),
                )
                if isinstance(ctx, vbu.SlashContext):
                    return await ctx.send(
                        f"Successfully created the sticker: {sticker.name}.", ephemeral=True
                    )
                await ctx.send(f"Successfully created the sticker: {sticker.name}.")
            except (discord.Forbidden, discord.HTTPException) as e:
                if isinstance(ctx, vbu.SlashContext):
                    return await ctx.send(
                        f"Failed to create the sticker due to: {e}", ephemeral=True
                    )
                await ctx.send(f"Failed to create the sticker due to: {e}")
        else:
            if isinstance(ctx, vbu.SlashContext):
                return await ctx.send("This message does not have a sticker.", ephemeral=True)
            await ctx.send("This message does not have a sticker.")


def setup(bot: vbu.Bot):
    x = StickerStealer(bot)
    bot.add_cog(x)
