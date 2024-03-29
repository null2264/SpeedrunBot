import os
from typing import TYPE_CHECKING, Optional

import aiohttp
import discord
from cassandra.cluster import Session
from discord.ext import commands
from speedrunpy.client import Client

from . import db
from .config import Config
from .context import MMContext


extensions = []
for filename in os.listdir("src/bot/exts"):
    if filename.endswith(".py"):
        extensions.append(f"src.bot.exts.{filename[:-3]}")


class MangoManBot(commands.Bot):
    if TYPE_CHECKING:
        db_session: Session

    def __init__(self):
        intents = discord.Intents.none()
        intents.messages = True  # for Fair and command execution
        intents.message_content = True  # for Fair and command execution
        intents.guild_reactions = True  # for starboard
        intents.guilds = True  # for RunGet

        super().__init__(
            command_prefix=["mm!"],
            case_insensitive=True,
            intents=intents,
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=("Over my Mangoes | Prefix mm!"),
            ),
            member_cache_flags=discord.MemberCacheFlags.none()
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

        try:
            self.db_session.shutdown()
        except AttributeError:
            pass
        await super().close()
        await self.src.close()
        await self.session.close()
