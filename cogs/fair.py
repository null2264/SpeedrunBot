import discord
import json
import unicodedata
import datetime
from datetime import timedelta
from pytz import exceptions, timezone
from discord.ext import commands

class Fair(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        bad_words = ["fair", "ⓕⓐⓘⓡ", "ɹıɐɟ","faİr", "justo", "adil"]
        count = 0
        fair = ""

        for word in bad_words:
            if word in message.content.lower().replace(" ", ""):
                # get fair object
                with open("fair.json", "r") as f:
                    fair = json.load(f)

                # if fairer's ID in fair.json
                userId = str(message.author.id)
                if userId in fair:
                    tz = fair[userId]["timezone"]
                    today = str(datetime.datetime.now(timezone(tz)).date())
                    yesterday = str(
                        datetime.datetime.now(timezone(tz)).date() - timedelta(1)
                    )

                    # if date in json != current date
                    date = fair[userId]["date"]
                    if date != today:
                        # increment fair day
                        fairDay = fair[userId]["day"] + 1

                        fairStreak = fair[userId]["streak"]
                        # if the user faired yesterday
                        if yesterday == date:
                            fairStreak = fair[userId]["streak"] + 1
                        else:
                            fairStreak = 1
                            await message.channel.send(
                                "streak lost. <:sad:716629485449117708>"
                            )

                        # only send && update if user is fairing for the first time today
                        fair[userId] = {
                            "day": fairDay,
                            "streak": fairStreak,
                            "date": today,
                            "timezone": tz,
                        }

                        fairInfo = f"day {fair[userId]['day']}, streak {fair[userId]['streak']}"
                        await message.channel.send(fairInfo)

                # new user - not in fair.json
                else:
                    # default to GMT
                    tz = "Europe/London"
                    today = str(datetime.datetime.now(timezone(tz)).date())
                    fair[userId] = {
                        "day": 1,
                        "streak": 1,
                        "date": today,
                        "timezone": tz,
                    }

                    fairInfo = (
                        f"day {fair[userId]['day']}, streak {fair[userId]['streak']}"
                    )
                    await message.channel.send(fairInfo)

                # overwrite with new fair object
                with open("fair.json", "w") as f:
                    json.dump(fair, f, indent=4)

                count += 1
                fairMsg = "Fair " * count
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

        # get fair object
        with open("fair.json", "r") as f:
            fair = json.load(f)

        # if this user has faired before
        userId = str(ctx.author.id)
        if userId not in fair:
            # new user
            await ctx.send("try saying 'fair' first")
            return

        try:
            # let users timezone = input timezone (string version so as to please json)
            # use timezone() simply to see if it's valid
            tz = str(timezone(timeZone))

        except exceptions.UnknownTimeZoneError:
            await ctx.send(
                "That's not a valid timezone. You can look them up at https://kevinnovak.github.io/Time-Zone-Picker/"
            )
            return

        # set user's timezone to (verified) input zone
        fair[userId]["timezone"] = tz

        # overwrite with new fair object
        with open("fair.json", "w") as f:
            json.dump(fair, f, indent=4)

        await ctx.send(
            f"{discord.utils.escape_mentions(ctx.message.author.display_name)} your timezone has been set to {timeZone}"
        )

def setup(bot):
    bot.add_cog(Fair(bot))