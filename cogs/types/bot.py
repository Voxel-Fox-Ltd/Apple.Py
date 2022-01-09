from typing import Dict

from discord.ext import vbu
from voxelbotutils.cogs.utils.types.config import BotConfig


class BotConfig(BotConfig):
    api_keys: Dict[str, str]


class Bot(vbu.Bot):
    config: BotConfig
