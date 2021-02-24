import time
from urllib.parse import quote, parse_qs, urlparse, urlencode
import hmac
from base64 import b64encode
import hashlib

import aiohttp
from aiohttp.web import HTTPFound, Request, RouteTableDef, json_response, Response
import aiohttp_session


routes = RouteTableDef()


def get_trello_oauth1_headers_and_params(request:Request, method:str, url:str, *, oauth_token:str=None, oauth_verifier:str=None, oauth_token_secret:str=None, oauth_callback_confirmed=None):
    # Oauth app keys
    client_consumer_key = request.app['config']['trello_oauth']['client_key']
    client_consumer_secret = request.app['config']['trello_oauth']['client_secret']

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


async def get_trello_oauth1_authorize_token(request):
    params, headers = get_trello_oauth1_headers_and_params(request, "POST", "https://trello.com/1/OAuthGetRequestToken")
    async with aiohttp.ClientSession() as session:
        site = await session.post(
            "https://trello.com/1/OAuthGetRequestToken",
            headers=headers,
            params=params,
        )
        return parse_qs(await site.text())


def get_trello_oauth1_login_url(request):
    params = {
        'key': request.app['config']['trello_oauth']['client_key'],
        'return_url': request.app['config']['website_base_url'].rstrip('/') + '/trello_login_callback',
        'callback_method': 'fragment',
        'scope': 'read,write,account',
        'expiration': 'never',
        'name': 'Apple.py',
        'response_type': 'token',
    }
    return f"https://www.trello.com/1/authorize?{urlencode(params)}"


@routes.get('/get_trello_login_url')
async def get_trello_login_url(request:Request):
    """
    Get the trello login url.
    """

    auth_url = get_trello_oauth1_login_url(request)
    return HTTPFound(location=auth_url)


@routes.get('/trello_login_callback')
async def trello_login_callback(request:Request):
    """
    Page the discord login redirects the user to when successfully logged in with trello.
    """

    text = (
        "<script>"
        "var params = new URLSearchParams ('?' + window.location.hash.slice(1)); "
        "window.location = `/trello_login_processor?${params.toString()}`;"
        "</script>"
    )
    return Response(
        body=text,
        content_type="text/html",
    )


@routes.get('/trello_login_processor')
async def trello_login_processor(request:Request):
    """
    Page the discord login redirects the user to when successfully logged in with trello.
    """

    session = await aiohttp_session.get_session(request)
    token = request.query.get("token", "")

    # Get their username
    params = {
        "token": token,
        "key": request.app['config']['trello_oauth']['client_key'],
    }
    async with aiohttp.ClientSession() as web_session:
        async with web_session.get("https://api.trello.com/1/members/me", params=params) as r:
            user_data = await r.json()

    # Store that
    async with request.app['database']() as db:
        await db(
            """INSERT INTO user_settings (user_id, trello_username, trello_token) VALUES ($1, $2, $3)
            ON CONFLICT (user_id) DO UPDATE SET trello_username=excluded.trello_username, trello_token=excluded.trello_token""",
            session['user_id'], user_data['username'], token,
        )
    return HTTPFound(location=session.pop('redirect_on_login', '/'))


@routes.get('/trello_logout')
async def trello_logout(request:Request):
    """
    Unlinks the user's account from trello
    """

    session = await aiohttp_session.get_session(request)
    async with request.app['database']() as db:
        await db(
            "UPDATE user_settings SET trello_username=NULL, trello_token=NULL WHERE user_id=$1",
            session['user_id']
        )
    return HTTPFound(location=session.pop('redirect_on_login', '/'))
