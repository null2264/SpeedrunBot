import asyncio


from bot import MangoManBot


try:
    import uvloop
except ImportError:
    pass
else:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


client = MangoManBot()


loop = asyncio.get_event_loop()
client.run()