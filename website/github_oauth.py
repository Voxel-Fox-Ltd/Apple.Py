import aiohttp
from aiohttp.web import HTTPFound, Request, RouteTableDef
import aiohttp_session


routes = RouteTableDef()


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
