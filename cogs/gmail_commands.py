from base64 import b64encode

from discord.ext import commands
import voxelbotutils as utils


class GmailCommands(utils.Cog):

    @utils.command()
    @commands.bot_has_permissions(send_messages=True)
    async def sendemail(self, ctx, email:str, *, body:str):
        """
        Send an email owo.
        """

        async with self.bot.database() as db:
            rows = await db("SELECT * FROM user_settings WHERE user_id=$1", ctx.author.id)
        if not rows or not rows[0]['google_access_token']:
            return await ctx.send(f"You need to login to Google to use this API - see `{ctx.clean_prefix}website`.")
        json = {"raw": b64encode(body.encode()).decode()}
        headers = {"Authorization": f"Bearer {rows[0]['google_access_token']}"}
        async with self.bot.session.get(f"https://gmail.googleapis.com/upload/gmail/v1/users/{email}/messages/send", json=json, headers=headers) as r:
            if str(r.status)[0] != '2':
                return await ctx.send("Failed to send email.")
        return await ctx.send("Email sent!")


def setup(bot:utils.Bot):
    x = GmailCommands(bot)
    bot.add_cog(x)
