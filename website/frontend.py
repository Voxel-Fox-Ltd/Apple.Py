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
        'response_type': 'code',
        'scope': 'channel:read:subscriptions',
    }

    # Github login URL params
    github_login_url_params = {
        'client_id': request.app['config']['github_oauth']['client_id'],
        'redirect_uri': request.app['config']['website_base_url'].rstrip('/') + '/github_login_processor',
        'scope': 'user repo',
    }

    # Gitlab login URL params
    gitlab_login_url_params = {
        'client_id': request.app['config']['gitlab_oauth']['client_id'],
        'redirect_uri': request.app['config']['website_base_url'].rstrip('/') + '/gitlab_login_processor',
        'response_type': 'code',
        'scope': 'read_user api read_api',
    }

    # Handle current logins
    session = await aiohttp_session.get_session(request)
    twitch_username = None
    github_username = None
    gitlab_username = None
    if session.get('logged_in'):
        async with request.app['database']() as db:
            rows = await db("SELECT * FROM user_settings WHERE user_id=$1", session['user_id'])
        if rows:
            twitch_username = rows[0]['twitch_username']
            github_username = rows[0]['github_username']
            gitlab_username = rows[0]['gitlab_username']

    # Return items
    return {
        'login_url': webutils.get_discord_login_url(request),
        'twitch_login_url': f'https://id.twitch.tv/oauth2/authorize?{urlencode(twitch_login_url_params)}',
        'twitch_username': twitch_username,
        'github_login_url': f'https://github.com/login/oauth/authorize?{urlencode(github_login_url_params)}',
        'github_username': github_username,
        'gitlab_login_url': f'https://gitlab.com/oauth/authorize?{urlencode(gitlab_login_url_params)}',
        'gitlab_username': gitlab_username,
    }
