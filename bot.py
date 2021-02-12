import aiohttp
import aiosqlite
import discord
import os


from discord.ext import commands


import config


class MangoManBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix= ["mm!"],
            case_insensitive=True,
            intents=discord.Intents.all(),
        )

        self.session = aiohttp.ClientSession()

        self.loop.create_task(self.asyncInit())
    
    async def asyncInit(self):
        """`__init__` but async"""
        self.db = await aiosqlite.connect("database.db")

        await self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS sent_runs
            (
                run_id TEXT UNIQUE
            )
            """
        )

        await self.db.commit()

    async def on_ready(self):
        await self.change_presence(
            activity = discord.Activity(
                type=discord.ActivityType.watching, 
                name=('Over my Mangoes | Prefix mm!')
            )
        )
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                self.load_extension(f'cogs.{filename[:-3]}')

    def run(self):
        super().run(config.token, reconnect=True)

    @property
    def config(self):
        return __import__("config")