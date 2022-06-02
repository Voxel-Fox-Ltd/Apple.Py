from typing import Dict

from discord.ext import vbu


class BotConfig(vbu.types.BotConfig):
    api_keys: Dict[str, str]


class Bot(vbu.Bot):
    config: BotConfig
