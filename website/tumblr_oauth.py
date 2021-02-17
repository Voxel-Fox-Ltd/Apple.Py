import time
from urllib.parse import quote, parse_qs, urlparse
import hmac
from base64 import b64encode
import hashlib

import aiohttp
from aiohttp.web import HTTPFound, Request, RouteTableDef
import aiohttp_session


routes = RouteTableDef()


def get_tumblr_oauth1_headers_and_params(request:Request, method:str, url:str, *, oauth_token:str=None, oauth_verifier:str=None, oauth_token_secret:str=None, oauth_callback_confirmed=None):
    # Oauth app keys
    client_consumer_key = request.app['config']['tumblr_oauth']['client_key']
    client_consumer_secret = request.app['config']['tumblr_oauth']['client_secret']

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


async def get_tumblr_oauth1_authorize_token(request):
    params, headers = get_tumblr_oauth1_headers_and_params(request, "POST", "https://www.tumblr.com/oauth/request_token")
    async with aiohttp.ClientSession() as session:
        site = await session.post(
            "https://www.tumblr.com/oauth/request_token",
            headers=headers,
            params=params,
        )
        return parse_qs(await site.text())


def get_tumblr_oauth1_login_url(token_data):
    return f"https://www.tumblr.com/oauth/authorize?oauth_token={token_data['oauth_token'][0]}"


async def get_tumblr_user_oauth1_token(request, oauth_data):
    params, headers = get_tumblr_oauth1_headers_and_params(request, "POST", "https://www.tumblr.com/oauth/access_token", **oauth_data)
    async with aiohttp.ClientSession() as session:
        site = await session.post(
            "https://www.tumblr.com/oauth/access_token",
            headers=headers,
            params=params,
        )
        return parse_qs(await site.text())


async def send_tumblr_oauth1_request(request, method, url, authed_user_params):
    params, headers = get_tumblr_oauth1_headers_and_params(request, method.upper(), f"https://api.tumblr.com/v2{url}", **authed_user_params)
    async with aiohttp.ClientSession() as session:
        site = await session.request(
            method.upper(),
            f"https://api.tumblr.com/v2{url}",
            headers=headers,
            params=params,
        )
        return await site.json()


@routes.get('/get_tumblr_login_url')
async def get_tumblr_login_url(request:Request):
    """
    Get the Tumblr login url.
    """

    session = await aiohttp_session.get_session(request)
    auth_token = await get_tumblr_oauth1_authorize_token(request)
    session['tumblr_oauth'] = auth_token
    auth_url = get_tumblr_oauth1_login_url(auth_token)
    return HTTPFound(location=auth_url)


@routes.get('/tumblr_login_processor')
async def tumblr_login_processor(request:Request):
    """
    Page the discord login redirects the user to when successfully logged in with Tumblr.
    """

    session = await aiohttp_session.get_session(request)
    query_data = session['tumblr_oauth']
    query_data.update(request.query)
    token_data = await get_tumblr_user_oauth1_token(request, query_data)
    # return json_response({'query_data': query_data, 'token_data': token_data})
    user_data = await send_tumblr_oauth1_request(request, "GET", "/user/info", token_data)
    # return json_response({'user_data': user_data, 'query_data': query_data, 'token_data': token_data})

    # Store that
    async with request.app['database']() as db:
        await db(
            """INSERT INTO user_settings (user_id, tumblr_username, tumblr_oauth_token, tumblr_oauth_token_secret) VALUES ($1, $2, $3, $4)
            ON CONFLICT (user_id) DO UPDATE SET tumblr_username=excluded.tumblr_username, tumblr_oauth_token=excluded.tumblr_oauth_token,
            tumblr_oauth_token_secret=excluded.tumblr_oauth_token_secret""",
            session['user_id'], urlparse(user_data['response']['user']['blogs'][0]['url']).hostname, token_data['oauth_token'][0], token_data['oauth_token_secret'][0],
        )
    return HTTPFound(location=session.pop('redirect_on_login', '/'))


@routes.get('/tumblr_logout')
async def tumblr_logout(request:Request):
    """
    Unlinks the user's account from Tumblr
    """

    session = await aiohttp_session.get_session(request)
    async with request.app['database']() as db:
        await db(
            "UPDATE user_settings SET tumblr_username=NULL, tumblr_oauth_token=NULL, tumblr_oauth_token_secret=NULL WHERE user_id=$1",
            session['user_id']
        )
    return HTTPFound(location=session.pop('redirect_on_login', '/'))
