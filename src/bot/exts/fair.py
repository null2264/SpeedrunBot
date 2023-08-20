import datetime
from datetime import timedelta

from discord.ext import commands
from pytz import timezone


class Fair(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.db

        self.bot.loop.create_task(self.asyncInit())

    async def asyncInit(self):
        """`__init__` but async"""
        # Create `fair_streak` table if its not exists
        await self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS fair_streak
            (
                user_id INTEGER UNIQUE,
                date TEXT NOT NULL,
                day INTEGER NOT NULL DEFAULT 0,
                streak INTEGER NOT NULL DEFAULT 0,
                timezone TEXT
            )
            """
        )
        await self.db.commit()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        bad_words = ["fair", "ⓕⓐⓘⓡ", "ɹıɐɟ", "faİr", "justo", "adil"]
        count = 0
        fair = ""

        for word in bad_words:
            # if member send "fair" or something similar
            if word in message.content.lower().replace(" ", ""):
                userId = message.author.id

                # Default values
                tz = "Europe/London"
                date = str(datetime.datetime.now(timezone(tz)).date())
                fairDay = 1
                fairStreak = 1
                streakLostMsg = "streak lost. <:sadge:796074093891682345>"
                fairMsg = "Fair"
                fairReplyMsg = "{} day {}, streak {}"
                changed = False

                async with self.db.execute("SELECT * FROM fair_streak WHERE user_id = (?)", (userId,)) as curr:
                    row = await curr.fetchone()
                    if row:
                        tz = row[4]
                        yesterday = str(datetime.datetime.now(timezone(tz)).date() - timedelta(1))
                        # Date from database
                        date = row[1]
                        fairDay = row[2]
                        fairStreak = row[3]
                    else:
                        # Insert user to fair_streak table if user_id not exist
                        await self.db.execute(
                            """
                            INSERT OR IGNORE INTO fair_streak VALUES (?, ?, ?, ?, ?)
                            """,
                            # (user_id, date, day, streak, timezone,)
                            (
                                userId,
                                date,
                                fairDay,
                                fairStreak,
                                tz,
                            ),
                        )
                        await self.db.commit()
                        # New "fairer"
                        changed = True
                    today = str(datetime.datetime.now(timezone(tz)).date())
                    if today != date:
                        fairDay += 1
                        if yesterday == date:
                            fairStreak += 1
                        else:
                            fairStreak = 1
                            await message.channel.send(streakLostMsg)
                        await self.db.execute(
                            """
                            UPDATE fair_streak
                            SET
                                date   = (?),
                                day    = (?),
                                streak = (?)
                            WHERE user_id = (?)
                            """,
                            (
                                today,
                                fairDay,
                                fairStreak,
                                userId,
                            ),
                        )
                        await self.db.commit()
                        changed = True
                    fairMsg = fairReplyMsg.format(fairMsg, fairDay, fairStreak) if changed else fairMsg
        try:
            await message.channel.send(fairMsg)
        except UnboundLocalError:
            pass

    # 24 hour cooldown
    # should probably be longer - we can't have these kids cheating!
    @commands.cooldown(1, 90000, commands.BucketType.user)
    @commands.command()
    async def timezone(self, ctx, timeZone):
        """`Set timezone for fair days/streaks`"""
        userId = ctx.author.id

        # Get data from database
        async with self.db.execute("SELECT * FROM fair_streak WHERE user_id = (?)", (userId,)) as curr:
            row = await curr.fetchone()
            if not row:
                return await ctx.send("Try saying 'fair' first!")

            tz = str(timezone(timeZone))

            await self.db.execute(
                """
                UPDATE fair_streak
                SET timezone = (?)
                WHERE user_id = (?)
                """,
                (userId, tz),
            )
            await self.db.commit()
            await ctx.reply("Your timezone has been set to `{}`".format(tz))


async def setup(bot):
    await bot.add_cog(Fair(bot))
