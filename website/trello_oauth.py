import time
from urllib.parse import quote, parse_qs, urlparse, urlencode
import hmac
from base64 import b64encode
import hashlib

import aiohttp
from aiohttp.web import HTTPFound, Request, RouteTableDef, json_response
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


def get_trello_oauth1_login_url(request, token_data):
    params = {
        # 'key': token_data['oauth_token'][0],
        'key': request.app['config']['trello_oauth']['client_key'],
        'return_url': request.app['config']['website_base_url'].rstrip('/') + '/trello_login_processor',
        'callback_method': 'fragment',
        'scope': 'read,write,account',
        'expiration': 'never',
        'name': 'Apple.py',
        'response_type': 'fragment',
    }
    return f"https://www.trello.com/1/authorize?{urlencode(params)}"


async def get_trello_user_oauth1_token(request, oauth_data):
    params, headers = get_trello_oauth1_headers_and_params(request, "POST", "https://trello.com/1/OAuthGetAccessToken", **oauth_data)
    async with aiohttp.ClientSession() as session:
        site = await session.post(
            "https://trello.com/1/OAuthGetAccessToken",
            headers=headers,
            params=params,
        )
        return parse_qs(await site.text())


async def send_trello_oauth1_request(request, method, url, authed_user_params):
    params, headers = get_trello_oauth1_headers_and_params(request, method.upper(), f"https://api.trello.com/1{url}", **authed_user_params)
    async with aiohttp.ClientSession() as session:
        site = await session.request(
            method.upper(),
            f"https://api.trello.com/v2{url}",
            headers=headers,
            params=params,
        )
        return await site.json()


@routes.get('/get_trello_login_url')
async def get_trello_login_url(request:Request):
    """
    Get the trello login url.
    """

    session = await aiohttp_session.get_session(request)
    auth_token = await get_trello_oauth1_authorize_token(request)
    session['trello_oauth'] = auth_token
    auth_url = get_trello_oauth1_login_url(request, auth_token)
    return HTTPFound(location=auth_url)


@routes.get('/trello_login_processor')
async def trello_login_processor(request:Request):
    """
    Page the discord login redirects the user to when successfully logged in with trello.
    """

    session = await aiohttp_session.get_session(request)
    # parsed_url = urlparse(request.url)
    fragment_data = parse_qs(request.rel_url.fragment)
    return json_response({'url': fragment_data})
    query_data = {'token': fragment_data['token'][0]}
    token_data = await get_trello_user_oauth1_token(request, query_data)
    # return json_response({'query_data': query_data, 'token_data': token_data})
    user_data = await send_trello_oauth1_request(request, "GET", "/members/me", token_data)
    return json_response({'user_data': user_data, 'query_data': query_data, 'token_data': token_data})

    # Store that
    async with request.app['database']() as db:
        await db(
            """INSERT INTO user_settings (user_id, trello_username, trello_oauth_token, trello_oauth_token_secret) VALUES ($1, $2, $3, $4)
            ON CONFLICT (user_id) DO UPDATE SET trello_username=excluded.trello_username, trello_oauth_token=excluded.trello_oauth_token,
            trello_oauth_token_secret=excluded.trello_oauth_token_secret""",
            session['user_id'], urlparse(user_data['response']['user']['blogs'][0]['url']).hostname, token_data['oauth_token'][0], token_data['oauth_token_secret'][0],
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
            "UPDATE user_settings SET trello_username=NULL, trello_oauth_token=NULL, trello_oauth_token_secret=NULL WHERE user_id=$1",
            session['user_id']
        )
    return HTTPFound(location=session.pop('redirect_on_login', '/'))
