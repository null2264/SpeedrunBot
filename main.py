import sys
import asyncio
from cassandra.cqlengine import connection
from dotenv import load_dotenv

try:
    import config  # type: ignore
except:
    config = None


from src.bot.core.bot import MangoManBot
from src.bot.core import db

load_dotenv()

bot = MangoManBot()
bot.load_config(config)


async def main():
    async with bot:
        bot.db_session = db.create_session(bot.config)
        await bot.run()


# REF: https://github.com/ZiRO-Bot/Z3R0/blob/29d1afe/src/main/__main__.py#L144-L155
# Use uvloop as loop policy if possible (Linux only)
try:
    import uvloop  # type: ignore - error is handled
except ImportError:
    asyncio.run(main())
else:
    if sys.version_info >= (3, 11):
        with asyncio.Runner(loop_factory=uvloop.new_event_loop) as runner:
            runner.run(main())
    else:
        uvloop.install()
        asyncio.run(main())
