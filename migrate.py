import asyncio
import json
import sqlite3
from aiocqlengine.query import AioBatchQuery
from src.bot.core.bot import MangoManBot
from src.bot.core import db
from dotenv import load_dotenv

try:
    import config  # type: ignore
except:
    config = None


async def main():
    load_dotenv()

    bot = MangoManBot()
    bot.load_config(config)

    con = sqlite3.connect("database.db")
    con.row_factory = sqlite3.Row

    session = db.create_session(bot.config)

    cur = con.cursor()

    res = cur.execute("SELECT * FROM fair_streak")
    fair = res.fetchall()
    batch = AioBatchQuery()
    for f in fair:
        db.FairStreak.batch(batch).create(user_id=f["user_id"], date=f["date"], day=f["day"], streak=f["streak"], timezone=f["timezone"])
    await batch.async_execute()

    res = cur.execute("SELECT * FROM sent_runs")
    runs = res.fetchall()
    batch = AioBatchQuery()
    count = 0
    for run in runs:
        db.RunSent.batch(batch).create(id=run["run_id"])
        count += 1
        if count >= 1000:
            await batch.async_execute()
            batch = AioBatchQuery()
            count = 0
    if batch.queries:
        await batch.async_execute()

    res = cur.execute("SELECT * FROM guilds")
    games = res.fetchall()
    batch = AioBatchQuery()
    for game in games:
        try:
            channel_id = int(game["channel_id"])
        except TypeError:
            channel_id = 0
        db.GameSubscribed.batch(batch).create(target_id=int(game["guild_id"]), channel_id=channel_id, id=game["game_id"], name=game["game_name"])
    await batch.async_execute()

    conf: dict = {}
    with open("starboard_config.json", "r") as fp:
        conf = json.load(fp)

    batch = AioBatchQuery()
    for guild, data in conf.items():
        guild: int = int(guild)
        data: dict
        db.Starboard.batch(batch).create(id=int(data["channel"]), guild_id=guild, amount=data["amount"])

        star_batch = AioBatchQuery()
        count = 0
        for star in data["pins"]:
            try:
                bot_msg = int(star[1])
            except TypeError:
                bot_msg = 0
            db.Starred.batch(star_batch).create(type=0, id=int(star[0]), guild_id=guild, bot_message_id=bot_msg, last_known_stars=data["amount"])
            count += 1
            if count >= 1000:
                await star_batch.async_execute()
                star_batch = AioBatchQuery()
                count = 0

        if star_batch.queries:
            await star_batch.async_execute()

    await batch.async_execute()

    session.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
