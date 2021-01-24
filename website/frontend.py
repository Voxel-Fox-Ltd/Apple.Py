from urllib.parse import urlencode

from aiohttp.web import HTTPFound, Request, RouteTableDef
from voxelbotutils import web as webutils
import aiohttp_session
import discord
from aiohttp_jinja2 import template


routes = RouteTableDef()


@routes.get("/")
@template("index.html.j2")
@webutils.add_discord_arguments()
async def index(request:Request):
    """
    Handle all the redirect URIs for the login links on the index.
    """

    # Twitch login URL params
    twitch_login_url_params = {
        'client_id': request.app['config']['twitch_oauth']['client_id'],
        'redirect_uri': request.app['config']['website_base_url'].rstrip('/') + '/twitch_login_processor',
        'response_type': 'token',
        'scope': 'channel:read:subscriptions',
    }

    # Handle current Twitch login
    session = await aiohttp_session.get_session(request)
    async with request.app['database']() as db:
        rows = await db("SELECT * FROM user_settings WHERE user_id=$1", session['user_id'])
    twitch_username = None
    if rows:
        twitch_username = rows[0]['twitch_username']

    # Return items
    return {
        'login_url': webutils.get_discord_login_url(request),
        'twitch_login_url': f'https://id.twitch.tv/oauth2/authorize?{urlencode(twitch_login_url_params)}',
        'twitch_username': twitch_username,
    }
