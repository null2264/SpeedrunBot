import asyncio
import aiohttp
import backoff
import discord
import json


from .utilities.formatting import realtime, pformat
from .utilities.paginator import MMReplyMenu
from .utilities.src import srcGame, srcRequest
from dateutil import parser
from discord.ext import commands, tasks, menus


class GameList(menus.ListPageSource):
    def __init__(self, ctx, data):
        self.ctx = ctx
        super().__init__(
            sorted(data),
            per_page=10,
        )

    def format_page(self, menu, games):
        target = self.ctx.message.guild or self.ctx.author
        e = discord.Embed(
            title="{}'s Watchlist".format(target.name),
            description="\n".join(" • {}".format(game) for game in games) or "No game being watched.",
            colour=discord.Colour.gold(),
        )
        return e


class RunGet(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.bot.loop.create_task(self.asyncInit())
        self.session = self.bot.session
        self.db = self.bot.db

    def ownerOrPerms(**perms):
        original = commands.has_permissions(**perms).predicate

        async def check(ctx):
            if not ctx.guild:
                return True
            return (
                ctx.author.id in ctx.bot.master
                or ctx.guild.owner_id == ctx.author.id
                or await original(ctx)
            )

        return commands.check(check)

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
                game_name TEXT,
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

        # The new self.games
        self.gameIds = {}
        async with self.db.execute("SELECT * FROM guilds") as curr:
            async for row in curr:
                rowDict = {"name": row[1], "targets": {row[2]: row[3]}}
                try:
                    self.gameIds[row[0]]["targets"].update(rowDict["targets"])
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
        """Handle recently verified runs"""
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
                # Get subcategory from run's variables
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
                    categoryName = levData["name"] + ": " + catData["name"]
                    leaderboard = await self.getLeaderboard(
                        run["game"]["data"]["id"], categoryID, levelID, subcategoryQuery
                    )
                else:
                    categoryName = catData["name"]
                    leaderboard = await self.getLeaderboard(
                        gameId=run["game"]["data"]["id"],
                        categoryId=categoryID,
                        subcategory=subcategoryQuery,
                    )
                # Get rank from leaderboard
                _ = leaderboard["data"]["runs"]
                for r in _:
                    if r["run"]["id"] == run["id"]:
                        rank = r["place"]
                # Add subcategory name to category name
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
                channels = [
                    ch if ch else user
                    for user, ch in self.gameIds[run["game"]["data"]["id"]][
                        "targets"
                    ].items()
                ]
                for targetId in channels:
                    target = self.bot.get_channel(targetId) or self.bot.get_user(
                        targetId
                    )
                    try:
                        await target.send(embed=a)
                    except discord.Forbidden:
                        # Bot have no permission
                        continue
            except KeyError as err:
                print(err)
                await self.removeRun(runId)
            except TypeError as err:
                # Something's wrong
                print(err)
                continue

    @tasks.loop(minutes=1.0)
    async def src_update(self):
        # Get and send recently verified runs
        futures = [self.getRecentlyVerified(offset) for offset in range(0, 2000, 200)]
        await asyncio.gather(*futures)

    @src_update.before_loop
    async def before_update(self):
        print("Getting runs...")
        await self.bot.wait_until_ready()

    @commands.command(aliases=["addgame"], usage="<game id|name|url> [#channel]")
    @ownerOrPerms(manage_guild=True)
    async def watchgame(self, ctx, game: srcGame, channel: discord.TextChannel = None):
        """Add a game to watchlist."""
        # TODO: Add ability to add multiple games
        isDM = ctx.message.guild is None

        if not isDM and not channel:
            return await ctx.reply("Usage: mm!watchgame <game id|name|url> [#channel]")

        # target id = user id for DM or guild id
        targetId = ctx.author.id if isDM else ctx.message.guild.id
        try:
            if targetId in self.gameIds[game.id]["targets"]:
                e = discord.Embed(
                    title="Already watching '{}'!".format(game.name),
                    colour=discord.Colour.gold(),
                )
                if (
                    not isDM
                    and channel.id != self.gameIds[game.id]["targets"][targetId]
                ):
                    # TODO: Add ability to replace channel id, use prompt (yes/no)
                    return await ctx.reply(embed=e)
                return await ctx.reply(embed=e)
            raise KeyError
        except KeyError:
            await self.db.execute(
                "INSERT INTO guilds VALUES (?, ?, ?, ?)",
                (game.id, game.name, targetId, None if isDM else channel.id),
            )
            await self.db.commit()
            targetDict = {
                "name": game.name,
                "targets": {targetId: None if isDM else channel.id},
            }
            try:
                self.gameIds[game.id]["targets"].update(targetDict["targets"])
            except KeyError:
                self.gameIds[game.id] = targetDict

            e = discord.Embed(
                title="'{}' has been added to watchlist".format(game.name),
                colour=discord.Colour.gold(),
            )
            e.set_thumbnail(url=game.cover)
            return await ctx.reply(embed=e)

    @commands.command(aliases=["deletegame"], usage="<game id|name|url>")
    @ownerOrPerms(manage_guild=True)
    async def unwatchgame(self, ctx, game: srcGame):
        """Remove a game from watchlist."""
        isDM = ctx.message.guild is None

        # target id = user id for DM or guild id
        targetId = ctx.author.id if isDM else ctx.message.guild.id

        try:
            if targetId not in self.gameIds[game.id]["targets"]:
                raise KeyError
        except KeyError:
            e = discord.Embed(
                title="'{}' is not in the watchlist!".format(game.name),
                colour=discord.Colour.gold(),
            )
            return await ctx.reply(embed=e)

        await self.db.execute(
            "DELETE FROM guilds WHERE game_id = ? AND guild_id = ?",
            (
                game.id,
                targetId,
            ),
        )
        await self.db.commit()
        self.gameIds[game.id]["targets"].pop(targetId)

        e = discord.Embed(
            title="'{}' has been removed from watchlist".format(game.name),
            colour=discord.Colour.gold(),
        )
        e.set_thumbnail(url=game.cover)
        return await ctx.reply(embed=e)

    @commands.command()
    async def gamelist(self, ctx):
        """Get game watchlist"""
        e = discord.Embed(
            title="<a:loading:776255339716673566> Loading...",
            colour=discord.Colour.gold(),
        )
        self.initMsg = await ctx.reply(embed=e)

        isDM = ctx.message.guild is None

        # target id = user id for DM or guild id
        targetId = ctx.author.id if isDM else ctx.message.guild.id

        guildGames = [
            game["name"]
            for game in self.gameIds.values()
            if targetId in game["targets"]
        ]

        pages = MMReplyMenu(
            source=GameList(ctx, guildGames),
            init_msg=self.initMsg,
            ping=True,
        )
        return await pages.start(ctx)


def setup(bot):
    bot.add_cog(RunGet(bot))
