from typing import Dict

from discord.ext import vbu


class BotConfig(vbu.custom_bot.BotConfig):
    api_keys: Dict[str, str]


class Bot(vbu.Bot):
    config: BotConfig
