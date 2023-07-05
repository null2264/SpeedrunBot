import sys
import asyncio


from bot import MangoManBot


bot = MangoManBot()


async def main():
    async with bot:
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
