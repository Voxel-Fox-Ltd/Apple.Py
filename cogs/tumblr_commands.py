import re
import time
from urllib.parse import quote
import hmac
import hashlib
from base64 import b64encode

import voxelbotutils as utils


def get_tumblr_oauth1_headers_and_params(config:dict, method:str, url:str, *, oauth_token:str=None, oauth_verifier:str=None, oauth_token_secret:str=None, oauth_callback_confirmed=None):
    # Oauth app keys
    client_consumer_key = config['api_keys']['tumblr']['client_key']
    client_consumer_secret = config['api_keys']['tumblr']['client_secret']

    # Standard params
    params = {
        "oauth_consumer_key": client_consumer_key,
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_nonce": str(int(time.time() * 1000)),
        "oauth_timestamp": str(int(time.time())),
    }

    # Add our other params
    if oauth_token_secret:
        if isinstance(oauth_token_secret, list):
            oauth_token_secret = oauth_token_secret[0]
        params.update({"oauth_token_secret": oauth_token_secret})
    if oauth_token:
        if isinstance(oauth_token, list):
            oauth_token = oauth_token[0]
        params.update({"oauth_token": oauth_token})
    if oauth_verifier:
        if isinstance(oauth_verifier, list):
            oauth_verifier = oauth_verifier[0]
        params.update({"oauth_verifier": oauth_verifier})

    # Build up the signature
    percent_encoded_params = {quote(i): quote(o) for i, o in params.items()}
    value_string = "&".join([f"{i}={percent_encoded_params[i]}" for i in sorted(percent_encoded_params.keys())])
    signature_base_string = f"{method.upper()}&{quote(url, safe='')}&{quote(value_string)}"
    if oauth_token_secret:
        signing_key = f"{client_consumer_secret}&{oauth_token_secret}"
    else:
        signing_key = f"{client_consumer_secret}&"
    encoded_signature = hmac.new(signing_key.encode(), signature_base_string.encode(), hashlib.sha1)
    signature = b64encode(encoded_signature.digest())

    # Work out our headers
    header_params = params.copy()
    header_params["oauth_signature"] = signature.decode()
    headers = {
        "Authorization": "OAuth " + ", ".join([f'{i}="{o}"' for i, o in header_params.items()]),
    }

    # Return data
    return params, headers


async def send_tumblr_oauth1_request(bot, method, url, authed_user_params, *, json:dict=None):
    params, headers = get_tumblr_oauth1_headers_and_params(bot.config, method.upper(), f"https://api.tumblr.com/v2{url}", **authed_user_params)
    site = await bot.session.request(
        method.upper(),
        f"https://api.tumblr.com/v2{url}",
        headers=headers,
        params=params,
        json=json,
    )
    return await site.json()


class TumblrCommands(utils.Cog):

    BLOG_URL = re.compile(r"https?://(?P<blog>[a-zA-Z0-9-]+\.tumblr\.com)/post/(?P<post>\d+)", re.IGNORECASE)

    @utils.command()
    async def reblog(self, ctx:utils.Context, *, url:str=None):
        """
        Reblogs a given tumblr url to your blog.
        """

        # See if they have an account linked
        async with self.bot.database() as db:
            user_rows = await db("SELECT * FROM user_settings WHERE user_id=$1", ctx.author.id)
        if not user_rows or user_rows[0]['tumblr_oauth_token'] is None:
            return await ctx.send(f"You need to link your Tumblr account to Discord to run this command - see `{ctx.clean_prefix}website`.")

        # See if the post is valid
        if not url:
            if not ctx.message.reference:
                raise utils.errors.MissingRequiredArgumentString("url")
            url = (await ctx.channel.fetch_message(ctx.message.reference.message_id)).content
        match = self.BLOG_URL.search(url)
        if not match:
            raise utils.errors.MissingRequiredArgumentString("url")

        # Sort our auth dict
        auth = {
            "oauth_token": user_rows[0]["tumblr_oauth_token"],
            "oauth_token_secret": user_rows[0]["tumblr_oauth_token_secret"],
        }

        # Get the post data
        post_data = await send_tumblr_oauth1_request(self.bot, "GET", f"/blog/{quote(match.group('blog'))}/posts/{match.group('post')}", auth)
        self.logger.info(post_data)
        json = {
            "parent_tumblelog_uuid": post_data["response"]["tumblelog_uuid"],
            "parent_post_id": post_data["response"]["id"],
            "reblog_key": post_data["response"]["reblog_key"],
        }

        # Try and reblog the item
        reblog_data = await send_tumblr_oauth1_request(self.bot, "POST", f"/blog/{quote(user_rows[0]['tumblr_username'])}/posts", auth, json=json)

        # Respond
        await ctx.send(f"Reblogged to your blog! <https://{user_rows[0]['tumblr_username']}/post/{reblog_data['response']['id']}>")


def setup(bot:utils.Bot):
    x = TumblrCommands(bot)
    bot.add_cog(x)
