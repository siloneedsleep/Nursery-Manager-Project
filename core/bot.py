import sqlite3
from typing import Tuple

import discord
from discord.ext import commands

from config.settings import settings
from core.database import DatabaseManager


class NurseryBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.all()

        super().__init__(
            command_prefix=commands.when_mentioned_or(*settings.prefixes),
            intents=intents,
            help_command=None,
            owner_id=settings.owner_id,
        )

        self.database = DatabaseManager(settings.db_path, settings.legacy_db_path)

    @property
    def conn(self) -> sqlite3.Connection:
        return self.database.conn

    def get_user_profile(self, user_id: int):
        return self.database.get_user_profile(user_id)

    def update_user_profile(
        self,
        user_id: int,
        candy: int = 0,
        bank: int = 0,
        xp: int = 0,
        mood: int = 0,
    ) -> Tuple[bool, int]:
        return self.database.update_user_profile(user_id, candy=candy, bank=bank, xp=xp, mood=mood)

    async def setup_hook(self) -> None:
        for extension in settings.extensions:
            await self.load_extension(extension)

    async def close(self) -> None:
        if getattr(self, "database", None) is not None:
            self.database.close()
        await super().close()


def build_bot() -> NurseryBot:
    return NurseryBot()