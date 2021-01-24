import aiohttp
from aiohttp.web import HTTPFound, Request, RouteTableDef
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
    access_token = request.query.get('access_token')

    # Validate that
    async with aiohttp.ClientSession() as web_session:
        async with web_session.get("https://id.twitch.tv/oauth2/validate", headers={"Authorization": f"Bearer {access_token}"}) as r:
            data = await r.json()
            if r.status != 200:
                return HTTPFound(location=session.pop('redirect_on_login', '/'))

    # Store that
    async with request.app['database']() as db:
        await db(
            """INSERT INTO user_settings (user_id, twitch_user_id, twitch_username, twitch_bearer_token) VALUES ($1, $2, $3, $4)
            ON CONFLICT (user_id) DO UPDATE SET twitch_user_id=excluded.twitch_user_id, twitch_username=excluded.twitch_username,
            twitch_bearer_token=excluded.twitch_bearer_token""",
            session['user_id'], data['user_id'], data['login'], access_token,
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
