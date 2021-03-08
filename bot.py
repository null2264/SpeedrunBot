import aiohttp
import aiosqlite
import discord
import os


from discord.ext import commands


import config

extensions = []
for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        extensions.append(f'cogs.{filename[:-3]}')

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

    async def on_ready(self):
        await self.change_presence(
            activity = discord.Activity(
                type=discord.ActivityType.watching, 
                name=('Over my Mangoes | Prefix mm!')
            )
        )
        for extension in extensions:
            self.load_extension(extension)

    def run(self):
        super().run(config.token, reconnect=True)
    
    async def close(self):
        for extension in extensions:
            try:
                self.unload_extension(extension)
            except Exception as e:
                print(e)
        
        await super().close()
        await self.db.close()

    @property
    def config(self):
        return __import__("config")