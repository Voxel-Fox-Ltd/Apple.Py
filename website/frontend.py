from urllib.parse import urlencode
import string
import random

from aiohttp.web import HTTPFound, Request, RouteTableDef, json_response
from voxelbotutils import web as webutils
import aiohttp_session
import discord
from aiohttp_jinja2 import template
import pytz


routes = RouteTableDef()


@routes.post("/set_timezone")
async def set_timezone(request:Request):
    """
    Sets the timezone for the given user.
    """

    session = await aiohttp_session.get_session(request)
    if not session.get("user_id"):
        return json_response({}, status=401)
    data = await request.json()
    if not data.get("timezone"):
        return json_response({}, status=401)
    try:
        timezone = pytz.timezone(data.get("timezone"))
    except pytz.UnknownTimeZoneError:
        return json_response({}, status=400)
    async with request.app['database']() as db:
        await db(
            """INSERT INTO user_settings (user_id, timezone_name) VALUES ($1, $2)
            ON CONFLICT (user_id) DO UPDATE SET timezone_name=excluded.timezone_name""",
            session['user_id'], data['timezone'],
        )
    return json_response({}, status=200)


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

    # Google login URL params
    google_login_url_params = {
        'client_id': request.app['config']['google_oauth']['client_id'],
        'redirect_uri': request.app['config']['website_base_url'].rstrip('/') + '/google_login_processor',
        'response_type': 'code',
        'scope': 'email https://www.googleapis.com/auth/gmail.send',
    }

    # Reddit login URL params
    reddit_login_url_params = {
        'client_id': request.app['config']['reddit_oauth']['client_id'],
        'redirect_uri': request.app['config']['website_base_url'].rstrip('/') + '/reddit_login_processor',
        'response_type': 'code',
        'scope': 'identity submit',
        'duration': 'permanent',
        'state': ''.join(random.choices(string.ascii_letters, k=64)),
    }

    # Handle current logins
    session = await aiohttp_session.get_session(request)
    timezone_name = None
    twitch_username = None
    github_username = None
    gitlab_username = None
    google_email = None
    tumblr_username = None
    reddit_username = None
    trello_username = None
    if session.get('logged_in'):
        async with request.app['database']() as db:
            rows = await db("SELECT * FROM user_settings WHERE user_id=$1", session['user_id'])
        if rows:
            timezone_name = rows[0]['timezone_name']
            twitch_username = rows[0]['twitch_username']
            github_username = rows[0]['github_username']
            gitlab_username = rows[0]['gitlab_username']
            google_email = rows[0]['google_email']
            tumblr_username = rows[0]['tumblr_username']
            reddit_username = rows[0]['reddit_username']
            trello_username = rows[0]['trello_username']

    # Return items
    return {
        'login_url': webutils.get_discord_login_url(request),

        'timezone_name': timezone_name,

        'twitch_login_url': f'https://id.twitch.tv/oauth2/authorize?{urlencode(twitch_login_url_params)}',
        'twitch_username': twitch_username,

        'github_login_url': f'https://github.com/login/oauth/authorize?{urlencode(github_login_url_params)}',
        'github_username': github_username,

        'gitlab_login_url': f'https://gitlab.com/oauth/authorize?{urlencode(gitlab_login_url_params)}',
        'gitlab_username': gitlab_username,

        'google_login_url': f'https://accounts.google.com/o/oauth2/v2/auth?{urlencode(google_login_url_params)}',
        'google_email': google_email,

        'tumblr_login_url': request.app['config']['website_base_url'].rstrip('/') + '/get_tumblr_login_url',
        'tumblr_username': tumblr_username,

        'reddit_login_url': f'https://www.reddit.com/api/v1/authorize?{urlencode(reddit_login_url_params)}',
        'reddit_username': reddit_username,

        'trello_login_url': request.app['config']['website_base_url'].rstrip('/') + '/get_trello_login_url',
        'trello_username': trello_username,
    }
