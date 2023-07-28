import os

import aiohttp
import asqlite
import config
import discord
from discord.ext import commands
from speedrunpy.client import Client

from .context import MMContext

extensions = []
for filename in os.listdir("./cogs"):
    if filename.endswith(".py"):
        extensions.append(f"cogs.{filename[:-3]}")


class MangoManBot(commands.Bot):
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

    async def get_context(self, message, *, cls=MMContext):
        return await super().get_context(message, cls=cls)

    async def setup_hook(self):
        self.db = await asqlite.connect("database.db")

        for extension in extensions:
            await self.load_extension(extension)

    async def run(self):
        await super().start(config.token, reconnect=True)

    async def close(self):
        for extension in extensions:
            try:
                await self.unload_extension(extension)
            except Exception as e:
                print(e)

        await super().close()
        await self.db.close()
        await self.src.close()
        await self.session.close()

    @property
    def config(self):
        return __import__("config")
