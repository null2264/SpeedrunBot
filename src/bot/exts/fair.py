import datetime
from datetime import timedelta

from discord.ext import commands
from pytz import timezone

from ..core import db


class Fair(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        bad_words = ["fair", "ⓕⓐⓘⓡ", "ɹıɐɟ", "faİr", "justo", "adil"]

        for word in bad_words:
            # if member send "fair" or something similar
            if word not in message.content.lower().replace(" ", ""):
                continue

            userId = message.author.id

            streakLostMsg = "streak lost. <:sadge:796074093891682345>"
            fairMsg = "Fair"
            fairReplyMsg = "{} day {}, streak {}"
            changed = False

            try:
                streak: db.FairStreak = await db.FairStreak.async_get(user_id=userId)

                yesterday: datetime.date = datetime.datetime.now(timezone(streak.timezone)).date() - timedelta(1)  # type: ignore
                today = datetime.datetime.now(timezone(streak.timezone)).date()  # type: ignore
                if today != streak.date:
                    streak.day += 1  # type: ignore
                    if yesterday == streak.date:
                        streak.streak += 1  # type: ignore
                    else:
                        streak.streak = 1  # type: ignore
                        await message.channel.send(streakLostMsg)
                    streak.date = today  # type: ignore
                    changed = True
                await streak.async_save()
            except db.FairStreak.DoesNotExist:
                streak = await db.FairStreak.async_create(
                    user_id=userId,
                    date=datetime.datetime.now(timezone("Europe/London")).date(),
                    day=1,
                    streak=1,
                    timezone="Europe/London",
                )
                changed = True

            fairMsg = fairReplyMsg.format(fairMsg, streak.day, streak.streak) if changed else fairMsg
            if changed:
                break

        try:
            await message.channel.send(fairMsg)  # type: ignore - Intended behaviour, handled by try-except
        except UnboundLocalError:
            pass

    # 24 hour cooldown
    # should probably be longer - we can't have these kids cheating!
    @commands.cooldown(1, 90000, commands.BucketType.user)
    @commands.command()
    async def timezone(self, ctx, timeZone):
        """`Set timezone for fair days/streaks`"""
        userId = ctx.author.id

        try:
            streak: db.FairStreak = await db.FairStreak.async_get(user_id=userId)
            streak.timezone = str(timezone(timeZone))  # type: ignore
            await streak.async_save()
            return await ctx.reply("Your timezone has been set to `{}`".format(streak.timezone))
        except db.FairStreak.DoesNotExist:
            return await ctx.send("Try saying 'fair' first!")


async def setup(bot):
    await bot.add_cog(Fair(bot))
