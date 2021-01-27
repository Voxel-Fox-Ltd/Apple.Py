import aiohttp
from aiohttp.web import HTTPFound, Request, RouteTableDef, json_response
from voxelbotutils import web as webutils
import aiohttp_session
import discord
from aiohttp_jinja2 import template


routes = RouteTableDef()


@routes.get('/login_processor')
async def login_processor(request:Request):
    """
    Page the discord login redirects the user to when successfully logged in with Discord.
    """

    await webutils.process_discord_login(request)
    session = await aiohttp_session.get_session(request)
    return HTTPFound(location=session.pop('redirect_on_login', '/'))


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


@routes.get('/github_login_processor')
async def github_login_processor(request:Request):
    """
    Page the discord login redirects the user to when successfully logged in with Github.
    """

    session = await aiohttp_session.get_session(request)

    # Validate that
    async with aiohttp.ClientSession() as web_session:
        params = {
            'client_id': request.app['config']['github_oauth']['client_id'],
            'client_secret': request.app['config']['github_oauth']['client_secret'],
            'code': request.query.get('code'),
            'redirect_uri': request.app['config']['website_base_url'].rstrip('/') + '/github_login_processor',
        }
        headers = {
            'Accept': 'application/vnd.github.v3+json',
        }
        async with web_session.post("https://github.com/login/oauth/access_token", params=params, headers=headers) as r:
            token_data = await r.json()
            if r.status != 200:
                return HTTPFound(location=session.pop('redirect_on_login', '/'))
        headers.update({"Authorization": f"token {token_data['access_token']}"})
        async with web_session.post("https://api.github.com/user", headers=headers) as r:
            user_data = await r.json()
            if r.status != 200:
                return HTTPFound(location=session.pop('redirect_on_login', '/'))

    # Store that
    async with request.app['database']() as db:
        await db(
            """INSERT INTO user_settings (user_id, github_username, github_access_token) VALUES ($1, $2, $3)
            ON CONFLICT (user_id) DO UPDATE SET github_username=excluded.github_username,
            github_access_token=excluded.github_access_token""",
            session['user_id'], user_data['login'], token_data['access_token'],
        )

    return HTTPFound(location=session.pop('redirect_on_login', '/'))


@routes.get('/github_logout')
async def github_logout(request:Request):
    """
    Unlinks the user's account from Github
    """

    session = await aiohttp_session.get_session(request)
    async with request.app['database']() as db:
        await db(
            "UPDATE user_settings SET github_username=NULL, github_access_token=NULL WHERE user_id=$1",
            session['user_id'],
        )
    return HTTPFound(location=session.pop('redirect_on_login', '/'))


@routes.get('/gitlab_login_processor')
async def gitlab_login_processor(request:Request):
    """
    Page the discord login redirects the user to when successfully logged in with Gitlab.
    """

    session = await aiohttp_session.get_session(request)

    # Validate that
    async with aiohttp.ClientSession() as web_session:
        params = {
            'client_id': request.app['config']['gitlab_oauth']['client_id'],
            'client_secret': request.app['config']['gitlab_oauth']['client_secret'],
            'code': request.query.get('code'),
            'redirect_uri': request.app['config']['website_base_url'].rstrip('/') + '/gitlab_login_processor',
            'grant_type': 'authorization_code',
        }
        async with web_session.post("https://gitlab.com/oauth/token", params=params) as r:
            token_data = await r.json()
            if r.status != 200:
                return HTTPFound(location=session.pop('redirect_on_login', '/'))
        headers = {'Authorization': f"Bearer {token_data['access_token']}"}
        async with web_session.get("https://gitlab.com/api/v4/user", headers=headers) as r:
            user_data = await r.json()
            if r.status != 200:
                return HTTPFound(location=session.pop('redirect_on_login', '/'))

    # Store that
    async with request.app['database']() as db:
        await db(
            """INSERT INTO user_settings (user_id, gitlab_username, gitlab_bearer_token, gitlab_refresh_token) VALUES ($1, $2, $3, $4)
            ON CONFLICT (user_id) DO UPDATE SET gitlab_username=excluded.gitlab_username,
            gitlab_bearer_token=excluded.gitlab_bearer_token, gitlab_refresh_token=excluded.gitlab_refresh_token""",
            session['user_id'], user_data['username'], token_data['access_token'], token_data['refresh_token'],
        )

    return HTTPFound(location=session.pop('redirect_on_login', '/'))


@routes.get('/gitlab_logout')
async def gitlab_logout(request:Request):
    """
    Unlinks the user's account from Gitlab
    """

    session = await aiohttp_session.get_session(request)
    async with request.app['database']() as db:
        await db(
            "UPDATE user_settings SET gitlab_username=NULL, gitlab_access_token=NULL WHERE user_id=$1",
            session['user_id']
        )
    return HTTPFound(location=session.pop('redirect_on_login', '/'))


@routes.get('/logout')
async def logout(request:Request):
    """
    Destroy the user's login session.
    """

    session = await aiohttp_session.get_session(request)
    session.invalidate()
    return HTTPFound(location='/')


@routes.get('/login')
async def login(request:Request):
    """
    Direct the user to the bot's Oauth login page.
    """

    return HTTPFound(location=webutils.get_discord_login_url(request, "/login_processor"))
