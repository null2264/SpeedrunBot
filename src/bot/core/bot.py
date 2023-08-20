import os
from typing import Optional, TYPE_CHECKING
from cassandra.cluster import Session

import aiohttp
import discord
from discord.ext import commands
from speedrunpy.client import Client

from . import db
from .config import Config
from .context import MMContext


extensions = []
for filename in os.listdir("./exts"):
    if filename.endswith(".py"):
        extensions.append(f"bot.exts.{filename[:-3]}")


class MangoManBot(commands.Bot):
    if TYPE_CHECKING:
        db_session: Session

    def __init__(self):
        super().__init__(
            command_prefix=["mm!"],
            case_insensitive=True,
            intents=discord.Intents.all(),
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=("Over my Mangoes | Prefix mm!"),
            ),
        )

        self.src = Client()
        self.session = aiohttp.ClientSession()

        self.master = (186713080841895936, 564610598248120320)
        self._config: Optional[Config] = None

    @property
    def config(self) -> Config:
        if not self._config:
            raise RuntimeError("Config is not yet loaded!")
        return self._config

    def load_config(self, config=None):
        try:
            self._config = Config(config.token, config.scylla_hosts, getattr(config, "scylla_port", None))
        except AttributeError:
            self._config = Config(
                os.getenv("DISCORD_TOKEN", ""),
                os.getenv("SCYLLA_HOSTS", " ").split(" "),
                int(os.getenv("SCYLLA_PORT", "0")),
            )

    async def get_context(self, message, *, cls=MMContext):
        return await super().get_context(message, cls=cls)

    async def setup_hook(self):
        for extension in extensions:
            await self.load_extension(extension)

    async def run(self):
        await super().start(self.config.token, reconnect=True)

    async def close(self):
        for extension in extensions:
            try:
                await self.unload_extension(extension)
            except Exception as e:
                print(e)

        self.db_session.shutdown()
        await super().close()
        await self.src.close()
        await self.session.close()
