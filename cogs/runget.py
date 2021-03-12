import asyncio
import aiohttp
import backoff
import discord
import json


from .utilities.formatting import realtime, pformat
from dateutil import parser
from discord.ext import commands, tasks


class RunGet(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # New self.games will look like this:
        # self.games = {
        #     "gameId": [channelId, channelId2],
        #     "gameId2": [channelId],
        # }
        self.games = (
            'k6q474zd', # Minecraft (Classic)
            '46w382n1', # Minecraft: Pocket Edition Lite
            'pd0wkq01', # Minecraft: New Nintendo 3DS Edition
            'k6q4520d', # Minecraft 4K
            '3dx2oz41', # Minecraft: Education Edition
            'j1nejgx1', # Minecraft: Pi Edition
            '4d792zz1', # ClassiCube
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

        # Try get sent_runs from database
        try:
            curr = await self.db.execute("SELECT * FROM sent_runs")
            rows = await curr.fetchall()
            self.sent_runs = [row[0] for row in rows]
        except Exception as exc:
            print("Something went wrong!", exc)
            self.sent_runs = []
        self.src_update.start()

    async def addRun(self, run_id: str):
        """Add run_id to sent_runs variable and sent_runs table"""
        self.sent_runs += [run_id]
        await self.db.execute(
            "INSERT OR IGNORE INTO sent_runs VALUES (?)",
            (run_id,)
        )
        await self.db.commit()
    
    async def removeRun(self, run_id: str):
        """Delete run_id from sent_runs variable and sent_runs table"""
        self.sent_runs -= [run_id]
        await self.db.execute(
            "DELETE FROM sent_runs WHERE run_id=?",
            (run_id,)
        )
        await self.db.commit()

    @backoff.on_exception(backoff.expo, aiohttp.ClientResponseError, max_tries=3, max_time=60)
    async def srcRequest(self, query):
        """Request info from speedrun.com.

        Use backoff to retry request when the request fails the first time 
        (Unless the error is 404 or 420 also ignore 200 because its not error)
        """
        async with self.session.get("https://www.speedrun.com/api/v1{}".format(query)) as res:
            if res.status not in (200, 420, 404):
                print("D:")
                raise aiohttp.ClientResponseError(res.request_info, res.history)
            _json = await res.json()
            return _json

    async def getLeaderboard(self, gameId, categoryId, levelId=None, subcategory: list=[]):
        """Get leaderboard info from speedrun.com"""
        leaderboard = {}
        if levelId:
            leaderboard = await self.srcRequest(
                "/leaderboards/{}/level/{}/{}?{}".format(
                    gameId, levelId, categoryId, '&'.join(subcategory)
                )
            )
        else:
            leaderboard = await self.srcRequest(
                "/leaderboards/{}/category/{}?{}".format(
                    gameId, categoryId, '&'.join(subcategory)
                )
            )
        return leaderboard

    async def getRecentlyVerified(self, offset, channel):
        """Handle recently verified runs

        channel argument is temporary,
        will be removed after per-server system implemented
        """
        # TODO: get channels from database
        runs_json = await self.srcRequest(f"/runs?status=verified&orderby=verify-date&direction=desc&max=200&embed=game,players,category.variables,level&offset={offset}")
        if not runs_json:
            print("Oof")
            return

        for run in runs_json['data']:    
            if run["game"]["data"]["id"] not in self.games:
                continue

            if run["id"] in self.sent_runs:
                continue

            runId = run["id"]
            gameName = run['game']['data']['names']['international']
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
                    foundVar = [c for c in catData["variables"]["data"] if c["id"] == var[0]]
                    if foundVar and foundVar[0]["is-subcategory"]:
                        subcategoryQuery += ["var-{}={}".format(var[0], var[1])]
                        subcategoryName += [foundVar[0]["values"]["values"][var[1]]["label"]]
                categoryID = catData["id"]
                if catData["type"] == "per-level":
                    levelID = levData["id"]
                    categoryName = levData["name"] + ": " + catData["name"] + " - " + ", ".join(subcategoryName)
                    leaderboard = await self.getLeaderboard(run['game']['data']['id'], categoryID, levelID, subcategoryQuery)
                    _ = leaderboard["data"]["runs"]
                    for r in _:
                        if r["run"]["id"] == run["id"]:
                            rank = r["place"]
                else:
                    categoryName = catData["name"]
                    leaderboard = await self.getLeaderboard(gameId=run['game']['data']['id'], categoryId=categoryID, subcategory=subcategoryQuery)
                    _ = leaderboard["data"]["runs"]
                    for r in _:
                        if r["run"]["id"] == run["id"]:
                            rank = r["place"]

            for player in run["players"]["data"]:
                if player["rel"] == "guest":
                    players.append(player["name"])
                else:
                    players.append(player["names"]["international"])

            try:
                a = discord.Embed(
                    title="{} by {}".format(realtime(igt if igt else rta), ', '.join(players)),
                    url=link,
                    colour=discord.Color(0xFFFFF0),
                    timestamp=parser.isoparse(playDate)
                )
                a.set_author(name="{} - {}".format(gameName, categoryName))
                a.add_field(name="Leaderboard Rank", value=str(rank))
                a.add_field(name="Verified at", value="`{}`".format(parser.isoparse(verifyDate)), inline=False)
                a.set_thumbnail(url=cover)

                await self.addRun(runId)
                await channel.send(embed=a)
            except KeyError as err:
                print(err)
                await self.removeRun(runId)
            except TypeError:
                # Something's wrong
                continue

    @tasks.loop(minutes=1.0)
    async def src_update(self):
        if self.bot.user.id in (810573928782757950, 733622032901603388):
            # Testing server
            channel = self.bot.get_guild(745481731133669476).get_channel(815600668396093461)
        else:
            # TODO: make this thing per-server
            channel = self.bot.get_guild(710400258793799681).get_channel(808445072948723732)

        # Get and send recently verified runs
        futures = [self.getRecentlyVerified(offset, channel) for offset in range(0, 2000, 200)]
        await asyncio.gather(*futures)

    @src_update.before_loop
    async def before_update(self):
        print('Getting runs...')
        await self.bot.wait_until_ready()

    @commands.command()
    async def watchgame(self, ctx, gameId: str = None):
        """Add a game to watchlist."""
        # TODO: Make converter to get gameId from game name/url
        await ctx.reply("Not yet implemented")

    @commands.command()
    async def unwatchgame(self, ctx, gameId: str = None):
        """Remove a game from watchlist."""
        await ctx.reply("Not yet implemented")


def setup(bot):
    bot.add_cog(RunGet(bot))
