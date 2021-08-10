import aiohttp
from aiohttp.web import HTTPFound, Request, RouteTableDef
import aiohttp_session


routes = RouteTableDef()


@routes.get('/twitch_login_processor')
async def twitch_login_processor(request:Request):
    """
    Page the discord login redirects the user to when successfully logged in with Twitch.
    """

    session = await aiohttp_session.get_session(request)

    # Validate that
    async with aiohttp.ClientSession() as web_session:
        params = {
            'client_id': request.app['config']['twitch_oauth']['client_id'],
            'client_secret': request.app['config']['twitch_oauth']['client_secret'],
            'code': request.query.get('code'),
            'grant_type': 'authorization_code',
            'redirect_uri': request.app['config']['website_base_url'].rstrip('/') + '/twitch_login_processor',
        }
        async with web_session.post("https://id.twitch.tv/oauth2/token", params=params) as r:
            token_data = await r.json()
            if r.status != 200:
                return HTTPFound(location=session.pop('redirect_on_login', '/'))
        async with web_session.get("https://id.twitch.tv/oauth2/validate", headers={"Authorization": f"Bearer {token_data['access_token']}"}) as r:
            validate_data = await r.json()
            if r.status != 200:
                return HTTPFound(location=session.pop('redirect_on_login', '/'))

    # Store that
    async with request.app['database']() as db:
        await db(
            """INSERT INTO user_settings (user_id, twitch_user_id, twitch_username, twitch_bearer_token) VALUES ($1, $2, $3, $4)
            ON CONFLICT (user_id) DO UPDATE SET twitch_user_id=excluded.twitch_user_id, twitch_username=excluded.twitch_username,
            twitch_bearer_token=excluded.twitch_bearer_token""",
            session['user_id'], validate_data['user_id'], validate_data['login'], token_data['access_token'],
        )

    return HTTPFound(location=session.pop('redirect_on_login', '/'))


@routes.get('/twitch_logout')
async def twitch_logout(request:Request):
    """
    Unlinks the user's account from Twitch
    """

    session = await aiohttp_session.get_session(request)
    async with request.app['database']() as db:
        await db(
            "UPDATE user_settings SET twitch_user_id=NULL, twitch_username=NULL, twitch_bearer_token=NULL WHERE user_id=$1",
            session['user_id']
        )
    return HTTPFound(location=session.pop('redirect_on_login', '/'))
