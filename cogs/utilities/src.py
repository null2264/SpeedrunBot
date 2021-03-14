import aiohttp
import backoff
import discord
import re


from discord.ext import commands


srcRegex = re.compile(r"https?:\/\/(?:www\.)?speedrun\.com\/(\w*)(?:\/|\#)?")


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
    async def convert(self, ctx, argument):
        # Get abbreviation from url
        match = srcRegex.fullmatch(argument)
        if match:
            argument = match.group(1)

        try:
            gameData = await srcRequest("/games/{}".format(argument))
        except KeyError:
            gameData = await srcRequest("/games?name={}".format(argument))
        finally:
            try:
                return Game(gameData["data"])
            except KeyError:
                raise GameNotFound(argument)
