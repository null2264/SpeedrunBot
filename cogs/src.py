import discord
import json


from dateutil import parser
from discord.ext import commands, tasks


def realtime(time):
    """
    Converts times in the format XXX.xxx into h m s ms
    """
    ms = int(time * 1000)
    s, ms = divmod(ms, 1000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    ms = "{:03d}".format(ms)
    s = "{:02d}".format(s)
    if h > 0:
        m = "{:02d}".format(m)
    return (
        ((h > 0) * (str(h) + "h "))
        + str(m)
        + "m "
        + str(s)
        + "s "
        + ((str(ms) + "ms") * (ms != "000"))
    )

class Speedrun(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.games = {'k6q474zd': "Minecraft (Classic)", '46w382n1': "Minecraft: Pocket Edition Lite", 'pd0wkq01': "Minecraft: New Nintendo 3DS Edition", 'k6q4520d': "Minecraft 4K", '3dx2oz41': "Minecraft: Education Edition", 'j1nejgx1': "Minecraft: Pi Edition", '4d792zz1': "ClassiCube"}
        self.client.loop.create_task(self.asyncInit())
        self.src_update.start()
        self.session = self.client.session
        self.db = self.client.db
    
    async def asyncInit(self):
        """`__init__` but async"""
        try:
            curr = await self.db.execute("SELECT * FROM sent_runs")
            rows = await curr.fetchall()
            self.sent_runs = [row[0] for row in rows]
        except Exception as exc:
            print("Something went wrong!", exc)
            self.sent_runs = []

    async def addRun(self, run_id: str):
        self.sent_runs += [run_id]
        await self.db.execute(
            """INSERT OR IGNORE INTO sent_runs VALUES (?)""",
            (run_id,)
        )
        await self.db.commit()

    @tasks.loop(minutes=1.0)
    async def src_update(self):

        # hardcoding this idc
        channel = self.client.get_guild(710400258793799681).get_channel(808445072948723732)

        # ZTS server
        # channel = self.client.get_guild(745481731133669476).get_channel(807494660745986050)

        page = 0
        for gameId in self.games.keys():
            while page < 10:
                offset = 200*page
                async with self.session.get(f"https://www.speedrun.com/api/v1/runs?game={gameId}&status=verified&orderby=verify-date&direction=desc&max=200&embed=game,players,category.variables,level&{offset}") as r:
                    try:
                        runs_json = json.loads(await r.text())
                    except json.decoder.JSONDecodeError:
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
                            a.add_field(name="Leaderboard Rank", value="Unknown" if not rank else rank)
                            a.add_field(name="Verified at", value=f"`{parser.isoparse(verifyDate)}`", inline=False)
                            a.set_thumbnail(url=cover)

                            await channel.send(embed=a)
                            await self.addRun(run["id"])
                        except KeyError as err:
                            print(err)
                            pass
                page += 1

    @src_update.before_loop
    async def before_update(self):
        print('Getting runs...')
        await self.client.wait_until_ready()


def setup(client):
    client.add_cog(Speedrun(client))
