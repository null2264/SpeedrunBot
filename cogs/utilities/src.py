import re

import aiohttp
import backoff
from discord.ext import commands

from ...context import MMContext

srcRegex = re.compile(r"https?:\/\/(?:www\.)?speedrun\.com\/(\w*)(?:\/.*|\#.*)?")
srcUserRegex = re.compile(
    r"https?:\/\/(?:www\.)?speedrun\.com\/user\/(\w*)(?:\/.*|\#.*)?"
)


@backoff.on_exception(
    backoff.expo, aiohttp.ClientResponseError, max_tries=3, max_time=60
)
async def srcRequest(query):
    """Request info from speedrun.com.

    Use backoff to retry request when the request fails the first time
    (Unless the error is 404 or 420 also ignore 200 because its not error)
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://www.speedrun.com/api/v1{}".format(query)
        ) as res:
            if res.status not in (200, 420, 404):
                print("D:")
                raise aiohttp.ClientResponseError(res.request_info, res.history)
            _json = await res.json()
            return _json


class Game(object):
    __slots__ = ("id", "name", "cover", "data")

    def __init__(self, data):
        self.id = data["id"]
        self.name = data["names"]["international"]
        self.cover = data["assets"]["cover-large"]["uri"]
        self.data = data

    def __getitem__(self, item):
        return self.data[item]

    def __str__(self):
        return self.name


class GameNotFound(commands.BadArgument):
    def __init__(self, argument):
        super().__init__(message='Game "{}" not Found'.format(argument))


class srcGame(commands.Converter):
    """Converter for speedrun.com game."""

    async def convert(self, ctx, argument):
        if argument is None:
            return None

        # Get abbreviation from url
        match = srcRegex.fullmatch(argument)
        if match:
            argument = match.group(1)

        gameData = await srcRequest("/games/{}".format(argument))
        if not gameData:
            gameData = await srcRequest("/games?name={}".format(argument))

        try:
            return Game(gameData["data"])
        except KeyError:
            raise GameNotFound(argument)


class srcGameLb(commands.Converter):
    """Converter for speedrun.com game.
    With embeds that useful for leaderboard command"""

    async def convert(self, ctx, argument):
        if argument is None:
            return None

        # Get abbreviation from url
        match = srcRegex.fullmatch(argument)
        if match:
            argument = match.group(1)

        # Embeds that useful for lb command
        argument += (
            "?embed=categories.variables,levels.variables,levels.categories.variables"
        )

        gameData = await srcRequest("/games/{}".format(argument))
        if not gameData:
            gameData = await srcRequest("/games?name={}".format(argument))

        try:
            return Game(gameData["data"])
        except KeyError:
            raise GameNotFound(argument)


class User(object):
    __slots__ = ("id", "name", "data")

    def __init__(self, data):
        self.id = data["id"]
        self.name = data["names"]["international"]
        self.data = data

    def __getitem__(self, item):
        return self.data[item]

    def __str__(self):
        return self.name


class UserNotFound(commands.BadArgument):
    def __init__(self, argument):
        super().__init__(message='User "{}" not Found'.format(argument))


class srcUser(commands.Converter):
    """Converter for speedrun.com user."""

    async def convert(self, ctx: MMContext, argument):
        if argument is None:
            return None

        # Get abbreviation from url
        match = srcUserRegex.fullmatch(argument)
        if match:
            argument = match.group(1)

        try:
            return ctx.bot.src.find_user(argument)
        except:
            raise UserNotFound(argument)
