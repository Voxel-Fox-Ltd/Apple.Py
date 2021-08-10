import aiohttp
from aiohttp.web import HTTPFound, Request, RouteTableDef
import aiohttp_session


routes = RouteTableDef()


@routes.get('/google_login_processor')
async def google_login_processor(request:Request):
    """
    Page the discord login redirects the user to when successfully logged in with Google.
    """

    session = await aiohttp_session.get_session(request)

    # Validate that
    async with aiohttp.ClientSession() as web_session:
        params = {
            'client_id': request.app['config']['google_oauth']['client_id'],
            'client_secret': request.app['config']['google_oauth']['client_secret'],
            'code': request.query.get('code'),
            'redirect_uri': request.app['config']['website_base_url'].rstrip('/') + '/google_login_processor',
            'grant_type': 'authorization_code',
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        async with web_session.post("https://oauth2.googleapis.com/token", data=params, headers=headers) as r:
            token_data = await r.json()
            if r.status != 200:
                return HTTPFound(location=session.pop('redirect_on_login', '/'))
        headers = {'Authorization': f"Bearer {token_data['access_token']}"}
        async with web_session.get("https://www.googleapis.com/oauth2/v1/userinfo", headers=headers) as r:
            user_data = await r.json()
            if r.status != 200:
                return HTTPFound(location=session.pop('redirect_on_login', '/'))

    # Store that
    async with request.app['database']() as db:
        await db(
            """INSERT INTO user_settings (user_id, google_email, google_access_token, google_refresh_token) VALUES ($1, $2, $3, $4)
            ON CONFLICT (user_id) DO UPDATE SET google_email=excluded.google_email,
            google_access_token=excluded.google_access_token, google_refresh_token=excluded.google_refresh_token""",
            session['user_id'], user_data['email'], token_data['access_token'], token_data.get('refresh_token'),
        )

    return HTTPFound(location=session.pop('redirect_on_login', '/'))


@routes.get('/google_logout')
async def google_logout(request:Request):
    """
    Unlinks the user's account from Google
    """

    session = await aiohttp_session.get_session(request)
    async with request.app['database']() as db:
        await db(
            "UPDATE user_settings SET gitlab_username=NULL, gitlab_bearer_token=NULL, gitlab_refresh_token=NULL WHERE user_id=$1",
            session['user_id']
        )
    return HTTPFound(location=session.pop('redirect_on_login', '/'))
