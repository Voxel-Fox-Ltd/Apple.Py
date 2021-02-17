from base64 import b64encode

import aiohttp
from aiohttp.web import HTTPFound, Request, RouteTableDef
import aiohttp_session


routes = RouteTableDef()


@routes.get('/reddit_login_processor')
async def reddit_login_processor(request:Request):
    """
    Page the discord login redirects the user to when successfully logged in with Reddit.
    """

    session = await aiohttp_session.get_session(request)

    # Validate that
    async with aiohttp.ClientSession() as web_session:
        auth = f"{request.app['config']['reddit_oauth']['client_id']}:{request.app['config']['reddit_oauth']['client_secret']}"
        headers = {
            'Authorization': f'Basic {b64encode(auth.encode()).decode()}',
        }
        params = {
            'code': request.query.get('code'),
            'grant_type': 'authorization_code',
            'redirect_uri': request.app['config']['website_base_url'].rstrip('/') + '/reddit_login_processor',
        }
        async with web_session.post("https://www.reddit.com/api/v1/access_token", data=params, headers=headers) as r:
            token_data = await r.json()
            if r.status != 200:
                return HTTPFound(location=session.pop('redirect_on_login', '/'))
        headers = {
            "Authorization": f"bearer {token_data['access_token']}",
            "User-Agent": "Apple.py Discord Bot (kae@voxelfox.co.uk)",
        }
        async with web_session.get("https://oauth.reddit.com/api/v1/me", headers=headers) as r:
            user_data = await r.json()
            if r.status != 200:
                return HTTPFound(location=session.pop('redirect_on_login', '/'))

    # Store that
    async with request.app['database']() as db:
        await db(
            """INSERT INTO user_settings (user_id, reddit_username, reddit_access_token, reddit_refresh_token) VALUES ($1, $2, $3, $4)
            ON CONFLICT (user_id) DO UPDATE SET reddit_username=excluded.reddit_username, reddit_access_token=excluded.reddit_access_token,
            reddit_refresh_token=excluded.reddit_refresh_token""",
            session['user_id'], user_data['name'], token_data['access_token'], token_data['refresh_token'],
        )

    return HTTPFound(location=session.pop('redirect_on_login', '/'))


@routes.get('/reddit_logout')
async def reddit_logout(request:Request):
    """
    Unlinks the user's account from Twitch
    """

    session = await aiohttp_session.get_session(request)
    async with request.app['database']() as db:
        await db(
            "UPDATE user_settings SET reddit_username=NULL, reddit_access_token=NULL, reddit_refresh_token=NULL WHERE user_id=$1",
            session['user_id']
        )
    return HTTPFound(location=session.pop('redirect_on_login', '/'))
