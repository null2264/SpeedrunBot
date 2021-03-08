import discord
import json


from .utilities.formatting import realtime, pformat
from dateutil import parser
from discord.ext import commands, tasks


class RunGetHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
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

    @tasks.loop(minutes=1.0)
    async def src_update(self):
        # hardcoding this idc
        if self.bot.user.id == 810573928782757950:
            # Testing server
            channel = self.bot.get_guild(745481731133669476).get_channel(807494660745986050)
        else:
            channel = self.bot.get_guild(710400258793799681).get_channel(808445072948723732)

        for gameId in self.games:
            for offset in range(0, 2000, 200):
                async with self.session.get(f"https://www.speedrun.com/api/v1/runs?game={gameId}&status=verified&orderby=verify-date&direction=desc&max=200&embed=game,players,category.variables,level&offset={offset}") as r:
                    try:
                        runs_json = json.loads(await r.text())
                    except json.decoder.JSONDecodeError as e:
                        print(e)
                        return
                    for run in runs_json['data']:
                        
                        if run["id"] in self.sent_runs:
                            continue

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
                            rank = ""
                            if catData["type"] == "per-level":
                                categoryID = catData["id"]
                                levelID = levData["id"]
                                categoryName = levData["name"] + ": " + catData["name"] + " - " + ", ".join(subcategoryName)
                                leaderboard = await self.session.get(f"https://www.speedrun.com/api/v1/leaderboards/{run['game']['data']['id']}/level/{levelID}/{categoryID}?{'&'.join(subcategoryQuery)}")
                                leaderboard = json.loads(await leaderboard.text())
                                _ = leaderboard["data"]["runs"]
                                for r in _:
                                    if r["run"]["id"] == run["id"]:
                                        rank = r["place"]
                            else:
                                categoryID = catData["id"]
                                categoryName = catData["name"]
                                leaderboard = await self.session.get(f"https://www.speedrun.com/api/v1/leaderboards/{run['game']['data']['id']}/category/{categoryID}?{'&'.join(subcategoryQuery)}")
                                leaderboard = json.loads(await leaderboard.text())
                                _ = leaderboard["data"]["runs"]
                                for r in _:
                                    if r["run"]["id"] == run["id"]:
                                        rank = r["place"]

                        players = []
                        for player in run["players"]["data"]:
                            if player["rel"] == "guest":
                                players.append(player["name"])
                            else:
                                players.append(player["names"]["international"])

                        igt = run["times"]["ingame_t"]
                        rta = run["times"]["realtime_t"]
                        cover = run["game"]["data"]["assets"]["cover-large"]["uri"]
                        verifyDate = run["status"]["verify-date"]
                        playDate = run["date"]
                        
                        try:
                            a = discord.Embed(
                                title=f"{realtime(igt if igt else rta)} by {', '.join(players)}",
                                url=link,
                                colour=discord.Color(0xFFFFF0),
                                timestamp=parser.isoparse(playDate)
                            )
                            a.set_author(name=f"{run['game']['data']['names']['international']} - {categoryName}")
                            a.add_field(name="Leaderboard Rank", value="-1 (Bot failed to get run's rank)" if not rank else rank)
                            a.add_field(name="Verified at", value=f"`{parser.isoparse(verifyDate)}`", inline=False)
                            a.set_thumbnail(url=cover)

                            await self.addRun(run["id"])
                            await channel.send(embed=a)
                        except KeyError as err:
                            print(err)
                            await self.removeRun(run["id"])

    @src_update.before_loop
    async def before_update(self):
        print('Getting runs...')
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(RunGetHandler(bot))
