import asyncio
import aiohttp
import backoff
import discord
import json


from .utilities.formatting import realtime, pformat
from dateutil import parser
from discord.ext import commands, tasks


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
    __slots__ = ("id", "name")
    def __init__(self, data):
        self.id = data["id"]
        self.name = data["names"]["international"]


class srcGame(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            gameData = await srcRequest("/games/{}".format(argument))
            return Game(gameData["data"])
        except KeyError:
            gameData = await srcRequest("/games?name={}".format(argument))
            return Game(gameData["data"])


class RunGet(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # New self.games will look like this:
        # self.games = {
        #     "gameId": [channelId, channelId2],
        #     "gameId2": [channelId],
        # }
        self.games = (
            "k6q474zd",  # Minecraft (Classic)
            "46w382n1",  # Minecraft: Pocket Edition Lite
            "pd0wkq01",  # Minecraft: New Nintendo 3DS Edition
            "k6q4520d",  # Minecraft 4K
            "3dx2oz41",  # Minecraft: Education Edition
            "j1nejgx1",  # Minecraft: Pi Edition
            "4d792zz1",  # ClassiCube
        )

        self.bot.loop.create_task(self.asyncInit())
        self.session = self.bot.session
        self.db = self.bot.db

    async def asyncInit(self):
        """`__init__` but async"""
        # Create `sent_runs` table if its not exists
        await self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS sent_runs
            (
                run_id TEXT UNIQUE
            )
            """
        )
        await self.db.commit()
        await self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS guilds
            (
                game_id TEXT,
                guild_id INTEGER,
                channel_id INTEGER
            )
            """
        )
        await self.db.commit()

        # Try get sent_runs from database
        try:
            async with self.db.execute("SELECT * FROM sent_runs") as curr:
                self.sent_runs = [row[0] async for row in curr]
        except Exception as exc:
            print("Something went wrong!", exc)
            self.sent_runs = []

        self.gameIds = {}
        async with self.db.execute("SELECT * FROM guilds") as curr:
            async for row in curr:
                rowDict = {row[1]: row[2]}
                try:
                    self.gameIds[row[0]].update(rowDict)
                except KeyError:
                    self.gameIds[row[0]] = rowDict

        self.src_update.start()

    async def addRun(self, run_id: str):
        """Add run_id to sent_runs variable and sent_runs table"""
        self.sent_runs += [run_id]
        await self.db.execute("INSERT OR IGNORE INTO sent_runs VALUES (?)", (run_id,))
        await self.db.commit()

    async def removeRun(self, run_id: str):
        """Delete run_id from sent_runs variable and sent_runs table"""
        self.sent_runs -= [run_id]
        await self.db.execute("DELETE FROM sent_runs WHERE run_id=?", (run_id,))
        await self.db.commit()

    async def getLeaderboard(
        self, gameId, categoryId, levelId=None, subcategory: list = []
    ):
        """Get leaderboard info from speedrun.com"""
        leaderboard = {}
        if levelId:
            leaderboard = await srcRequest(
                "/leaderboards/{}/level/{}/{}?{}".format(
                    gameId, levelId, categoryId, "&".join(subcategory)
                ),
            )
        else:
            leaderboard = await srcRequest(
                "/leaderboards/{}/category/{}?{}".format(
                    gameId, categoryId, "&".join(subcategory)
                ),
            )
        return leaderboard

    async def getRecentlyVerified(self, offset):
        """Handle recently verified runs

        channel argument is temporary,
        will be removed after per-server system implemented
        """
        # TODO: get channels from database
        runs_json = await srcRequest(
            f"/runs?status=verified&orderby=verify-date&direction=desc&max=200&embed=game,players,category.variables,level&offset={offset}",
        )
        if not runs_json:
            print("Oof")
            return

        for run in runs_json["data"]:
            if run["game"]["data"]["id"] not in self.gameIds.keys():
                continue

            if run["id"] in self.sent_runs:
                continue

            runId = run["id"]
            gameName = run["game"]["data"]["names"]["international"]
            cover = run["game"]["data"]["assets"]["cover-large"]["uri"]
            verifyDate = run["status"]["verify-date"]
            players = []
            rank = "-1 (Bot failed to get run's rank)"
            igt = run["times"]["ingame_t"]
            rta = run["times"]["realtime_t"]
            playDate = run["date"]
            link = run["weblink"]
            levData = run["level"]["data"]
            catData = run["category"]["data"]

            runVars = run["values"]
            if catData:
                subcategoryQuery = []
                subcategoryName = []
                for var in runVars.items():
                    foundVar = [
                        c for c in catData["variables"]["data"] if c["id"] == var[0]
                    ]
                    if foundVar and foundVar[0]["is-subcategory"]:
                        subcategoryQuery += ["var-{}={}".format(var[0], var[1])]
                        subcategoryName += [
                            foundVar[0]["values"]["values"][var[1]]["label"]
                        ]
                categoryID = catData["id"]
                if catData["type"] == "per-level":
                    levelID = levData["id"]
                    categoryName = (
                        levData["name"]
                        + ": "
                        + catData["name"]
                    )
                    leaderboard = await self.getLeaderboard(
                        run["game"]["data"]["id"], categoryID, levelID, subcategoryQuery
                    )
                    _ = leaderboard["data"]["runs"]
                    for r in _:
                        if r["run"]["id"] == run["id"]:
                            rank = r["place"]
                else:
                    categoryName = catData["name"]
                    categoryName = (
                        catData["name"]
                    )
                    leaderboard = await self.getLeaderboard(
                        gameId=run["game"]["data"]["id"],
                        categoryId=categoryID,
                        subcategory=subcategoryQuery,
                    )
                    _ = leaderboard["data"]["runs"]
                    for r in _:
                        if r["run"]["id"] == run["id"]:
                            rank = r["place"]
                if subcategoryName:
                    categoryName += " - " + ", ".join(subcategoryName)

            for player in run["players"]["data"]:
                if player["rel"] == "guest":
                    players.append(player["name"])
                else:
                    players.append(player["names"]["international"])

            try:
                a = discord.Embed(
                    title="{} by {}".format(
                        realtime(igt if igt else rta), ", ".join(players)
                    ),
                    url=link,
                    colour=discord.Color(0xFFFFF0),
                    timestamp=parser.isoparse(playDate),
                )
                a.set_author(name="{} - {}".format(gameName, categoryName))
                a.add_field(name="Leaderboard Rank", value=str(rank))
                a.add_field(
                    name="Verified at",
                    value="`{}`".format(parser.isoparse(verifyDate)),
                    inline=False,
                )
                a.set_thumbnail(url=cover)

                await self.addRun(runId)
                channels = [ch if ch else user for user, ch in self.gameIds[run["game"]["data"]["id"]].items()]
                for target in channels:
                    target = self.bot.get_channel(target) or self.bot.get_user(target)
                    await target.send(embed=a)
            except KeyError as err:
                print(err)
                await self.removeRun(runId)
            except TypeError as err:
                # Something's wrong
                print(err)
                continue

    @tasks.loop(minutes=1.0)
    async def src_update(self):
        if self.bot.user.id in (810573928782757950, 733622032901603388):
            # Testing server
            channel = self.bot.get_guild(745481731133669476).get_channel(
                815600668396093461
            )
        else:
            # TODO: make this thing per-server
            channel = self.bot.get_guild(710400258793799681).get_channel(
                808445072948723732
            )

        # Get and send recently verified runs
        futures = [
            self.getRecentlyVerified(offset) for offset in range(0, 2000, 200)
        ]
        await asyncio.gather(*futures)

    @src_update.before_loop
    async def before_update(self):
        print("Getting runs...")
        await self.bot.wait_until_ready()

    @commands.command()
    async def watchgame(self, ctx, game: srcGame, channel: discord.TextChannel = None):
        """Add a game to watchlist."""
        isDM = ctx.message.guild is None

        if not isDM and not channel:
            return await ctx.reply("Usage: mm!watchgame <game id> [#channel]")

        # target id = user id for DM or guild id
        targetId = ctx.author.id if isDM else ctx.message.guild.id
        try:
            if targetId in self.gameIds[game.id]:
                if not isDM and channel.id != self.gameIds[game.id][targetId]:
                    # TODO: Add ability to replace channel id, use prompt (yes/no)
                    return await ctx.reply("Already watching this game!")
                return await ctx.reply("Already watching this game!")
            raise KeyError
        except KeyError:
            await self.db.execute(
                "INSERT INTO guilds VALUES (?, ?, ?)", (
                    game.id, 
                    targetId,
                    None if isDM else channel.id
                )
            )
            await self.db.commit()
            targetDict = {targetId: None if isDM else channel.id}
            try:
                self.gameIds[game.id].update(targetDict)
            except KeyError:
                self.gameIds[game.id] = targetDict
            return await ctx.reply("{} has been added to watchlist".format(game.name))

    @commands.command()
    async def unwatchgame(self, ctx, game: srcGame):
        """Remove a game from watchlist."""
        isDM = ctx.message.guild is None

        # target id = user id for DM or guild id
        targetId = ctx.author.id if isDM else ctx.message.guild.id
        
        try:
            if targetId not in self.gameIds[game.id]:
                raise KeyError
        except KeyError:
            return await ctx.reply("{} is not in the watchlist!".format(game.name))

        await self.db.execute(
            "DELETE FROM guilds WHERE game_id = ? AND guild_id = ?", (
                game.id, 
                targetId,
            )
        )
        await self.db.commit()
        self.gameIds[game.id].pop(targetId)
        return await ctx.reply("{} has been removed from watchlist".format(game.name))


def setup(bot):
    bot.add_cog(RunGet(bot))
