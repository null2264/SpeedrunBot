import asyncio
import aiohttp
import discord
import json
import re


from .utilities.formatting import realtime, pformat
from .utilities.paginator import MMMenu, MMReplyMenu
from .utilities.src import (
    srcGame,
    srcGameLb,
    srcRequest,
    srcUser,
    UserNotFound,
    GameNotFound
)
from dateutil import parser
from discord.ext import commands, menus
from speedrunpy import SpeedrunPy, errors as srcError


class CategoriesPageSource(menus.ListPageSource):
    def __init__(self, ctx, data):
        """PageSource for sr.c Categories"""
        self.ctx = ctx
        self.data = data
        cats = data.rawData["categories"]["data"]
        super().__init__(
            [cat for cat in cats if cat["type"] == "per-game"],
            per_page=1,
        )

    def format_page(self, menu, category):
        e = discord.Embed(
            title=category["name"],
            description=category["rules"],
            colour=discord.Colour.gold(),
        )
        e.set_author(
            name=self.data.name,
            icon_url="https://www.speedrun.com/images/1st.png",
        )
        e.set_thumbnail(url=self.data.assets["cover-large"].uri)
        e.set_footer(
            text="Requested by {}".format(str(self.ctx.author)),
            icon_url=self.ctx.author.avatar_url,
        )
        vars = category["variables"]["data"]
        for var in vars:
            if not var["is-subcategory"]:
                continue
            for val in var["values"]["values"].values():
                e.add_field(
                    name=val["label"],
                    value=val["rules"] or "No rules specified.",
                    inline=False if val["rules"] else True,
                )
        return e


class LeaderboardPageSource(menus.ListPageSource):
    def __init__(self, ctx, data):
        """PageSource for sr.c Leaderboard"""
        self.ctx = ctx
        self.data = data["data"]
        self.gameData = self.data["game"]["data"]
        self.playerData = {}
        for player in self.data["players"]["data"]:
            if player["rel"] == "guest":
                continue
            if player["id"] not in self.playerData:
                self.playerData[player["id"]] = player

        self.catName = [self.data["category"]["data"]["name"]]
        if self.data["level"]["data"]:
            self.catName.insert(0, self.data["level"]["data"]["name"])

        self.varName = []
        for value in self.data["values"]:
            for variable in self.data["variables"]["data"]:
                if variable["id"] == value:
                    self.varName += [
                        variable["values"]["values"][self.data["values"][value]][
                            "label"
                        ]
                    ]

        self.catName = ": ".join(self.catName)
        if self.varName:
            self.catName += " - " + ", ".join(self.varName)

        super().__init__(self.data["runs"], per_page=9)

    async def format_page(self, menu, runs):
        e = discord.Embed(
            title="{}".format(self.catName),
            colour=discord.Colour.gold(),
        )
        e.set_author(
            name=self.gameData["names"]["international"] + " - Leaderboard",
            icon_url="https://www.speedrun.com/images/1st.png",
        )
        e.set_thumbnail(url=self.gameData["assets"]["cover-large"]["uri"])
        e.set_footer(
            text="Requested by {}".format(str(self.ctx.author)),
            icon_url=self.ctx.author.avatar_url,
        )

        for run in runs:
            players = []
            for player in run["run"]["players"]:
                if player["rel"] == "guest":
                    players += [player["name"]]
                else:
                    players += [self.playerData[player["id"]]["names"]["international"]]

            e.add_field(
                name="{}. {}".format(run["place"], ", ".join(players)),
                value=realtime(run["run"]["times"]["primary_t"]),
            )
        return e


class SRC(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.src = SpeedrunPy(session=self.session)
        self.reLevelAndCat = re.compile(r"(.*)\((.*)\)")
        self.baseUrl = "https://www.speedrun.com/api/v1"

    async def getVerified(self, user, game, offset):
        userID = user.id
        userName = user.name

        params = {"examiner": userID, "page": 0, "perPage": 200}
        if game:
            # Get game id if game is specified
            params["game"] = game.id

        async with self.session.get(
            self.baseUrl
            + "/runs?examiner={}&offset={}&max=200".format(userID, offset)
            + ("&game={}".format(game.id) if game else "")
        ) as runs:
            runs = await runs.json()
            return runs["pagination"]["size"]

    @commands.command(aliases=["v"])
    async def verified(self, ctx, user: srcUser, game: srcGame = None):
        """Gets how many runs a user has verified."""
        e = discord.Embed(
            title="<a:loading:776255339716673566> Loading... (SRC API sucks so its going to take a while)",
            colour=discord.Colour.gold(),
        )
        initMsg = await ctx.reply(embed=e)

        # Get verified runs examined by {user}
        futures = [
            self.getVerified(user, game, offset) for offset in range(0, 5000, 200)
        ]
        runs = await asyncio.gather(*futures)

        e = discord.Embed(
            title="User: {}".format(user.name),
            description="Runs verified:\n `{}`".format(sum(runs)),
            colour=discord.Colour.gold(),
        )
        e.set_author(
            name="speedrun.com",
            icon_url="https://www.speedrun.com/images/1st.png",
        )
        e.set_thumbnail(
            url="https://www.speedrun.com/themes/user/{}/image.png".format(user.name)
        )
        await initMsg.edit(embed=e)

    @verified.error
    async def verifiedError(self, ctx, error):
        error = getattr(error, "original", error)
        if isinstance(error, UserNotFound):
            e = discord.Embed(
                title="<:error:783265883228340245> 404 - User not found!",
                colour=discord.Colour.red(),
            )
            return await ctx.reply(embed=e)
        if isinstance(error, GameNotFound):
            e = discord.Embed(
                title="<:error:783265883228340245> 404 - Game not found!",
                colour=discord.Colour.red(),
            )
            return await ctx.reply(embed=e)

    async def get_user_id(self, username):
        data = await self.src.get("/users/", f"{username}")
        if "data" not in data:
            return None
        data = data["data"]
        return data["id"]

    async def username(self, user_id):
        data = await self.src.get("/users/", f"{user_id}")
        if "data" not in data:
            return None
        data = data["data"]
        return data["names"]["international"]

    @commands.command(name="wrcount", aliases=["wrs"])
    async def wrcount(self, ctx, user: str):
        """Counts the number of world records a user has."""
        e = discord.Embed(
            title="<a:loading:776255339716673566> Loading... (SRC API sucks so its going to take a while)",
            colour=discord.Colour.gold(),
        )
        msg = await ctx.send(embed=e)

        data = await self.src.get("/users", "/{}/personal-bests".format(user))
        try:
            data = data["data"]
        except KeyError:
            return await ctx.send(f"There's no user called `{user}`")

        fullgame_wr = sum(
            [1 for pb in data if pb["place"] == 1 and not pb["run"]["level"]]
        )
        ils_wr = sum([1 for pb in data if pb["place"] == 1 and pb["run"]["level"]])

        userName = await self.username(await self.get_user_id(user))

        e = discord.Embed(
            title="{}'s World Records".format(userName),
            description="Full games: `{}`\nIndividual levels: `{}`\n**Total: `{}`**".format(
                fullgame_wr, ils_wr, fullgame_wr + ils_wr
            ),
            colour=discord.Colour.gold(),
        )
        e.set_author(
            name="speedrun.com",
            icon_url="https://www.speedrun.com/images/1st.png",
        )
        e.set_thumbnail(
            url="https://www.speedrun.com/themes/user/{}/image.png".format(userName)
        )

        await msg.edit(embed=e)

    @commands.group(aliases=["gm"], example=["group"], invoke_without_command=True)
    async def gamemoderatorsof(self, ctx, arg=None):
        """Figure out who the Game Moderators of a game are."""
        embed = discord.Embed(
            title="<:error:783265883228340245>  **Error!**",
            description="**Argument (game) not specified. Try using one of these games**",
            color=0xEC0909,
        )
        embed.add_field(name="Minecraft (Classic)", value="mcc", inline=True)
        embed.add_field(name="Classicube", value="cc", inline=True)
        embed.add_field(
            name="Minecraft: New Nintendo 3DS Edition", value="mc3ds", inline=True
        )
        embed.add_field(
            name="Minecraft: Pocket Edition Lite", value="mclite", inline=True
        )
        embed.add_field(name="Minecraft: Education Edition", value="mcee", inline=True)
        embed.add_field(name="Minecraft 4K", value="mc4k", inline=True)
        embed.add_field(name="Minecraft: Pi Edition", value="mcpi", inline=True)

        await ctx.send(embed=embed)

    @gamemoderatorsof.command(name="mcc")
    async def mcc(self, ctx):
        """`Minecraft (Classic) Game Moderators`"""
        a = discord.Embed(
            colour=discord.Color(0xE41919),
            title="**Minecraft (Classic) Game Moderators**",
            description="<:SuperMod:808405808793911316> ReniSR (<@577935851154046998>)\n"
            + "<:SuperMod:808405808793911316> Insert (<@727035417039339540>)\n"
            + "<:SuperMod:808405808793911316> Riley (<@168531454463049728>)\n"
            + "<:SuperMod:808405808793911316> DarkSRC (<@595742728248360960>)\n"
            + "<:Moderator:808405808768614460> IKY (<@564610598248120320>)\n"
            + "<:Moderator:808405808768614460> Kai. (<@447818513906925588>)\n"
            + "<:Moderator:808405808768614460> skye (<@329538915805691905>)\n"
            + "<:Moderator:808405808768614460> ThanksDude (<@435314420638416917>)\n"
            + "<:Moderator:808405808768614460> Creeper (<@286286473924444162>)\n"
            + "<:Moderator:808405808768614460> alexwaslost (<@686940596257947664>)\n"
            + "<:Moderator:808405808768614460> Quivvy (<@359110554721189889>)\n"
            + "<:Moderator:808405808768614460> DimitrovN (<@509800865172029470>)\n"
            + "<:Moderator:808405808768614460> NeonTrtl (<@571733724547252227>)\n",
        )
        await ctx.send(embed=a)

    @gamemoderatorsof.command(name="cc")
    async def cc(self, ctx):
        """`Classicube Game Moderators`"""
        a = discord.Embed(
            colour=discord.Color(0xE41919),
            title="**Classicube Game Moderators**",
            description="<:SuperMod:808405808793911316> ReniSR (<@577935851154046998>)\n"
            + "<:Moderator:808405808768614460> Insert (<@727035417039339540>)\n"
            + "<:Moderator:808405808768614460> Riley (<@168531454463049728>)\n"
            + "<:Moderator:808405808768614460> Kai. (<@447818513906925588>)\n",
        )
        await ctx.send(embed=a)

    @gamemoderatorsof.command(name="mc3ds")
    async def mc3ds(self, ctx):
        """`Minecraft: New Nintendo 3DS Edition Game Moderators`"""
        a = discord.Embed(
            colour=discord.Color(0xE41919),
            title="**Minecraft: New Nintendo 3DS Edition Game Moderators**",
            description="<:SuperMod:808405808793911316> ReniSR (<@577935851154046998>)\n"
            + "<:SuperMod:808405808793911316> Insert (<@727035417039339540>)\n"
            + "<:SuperMod:808405808793911316> Riley (<@168531454463049728>)\n"
            + "<:SuperMod:808405808793911316> DarkSRC (<@595742728248360960>)\n"
            + "<:Moderator:808405808768614460> Khalooody (<@366219142799556620>)\n"
            + "<:Moderator:808405808768614460> blunderpolicy (<@306969912566611968>)\n",
        )
        await ctx.send(embed=a)

    @gamemoderatorsof.command(name="mclite")
    async def mclite(self, ctx):
        """`Minecraft: Pocket Edition Lite Game Moderators`"""
        a = discord.Embed(
            colour=discord.Color(0xE41919),
            title="**Minecraft: Pocket Edition Lite Game Moderators**",
            description="<:SuperMod:808405808793911316> ReniSR (<@577935851154046998>)\n"
            + "<:SuperMod:808405808793911316> Insert (<@727035417039339540>)\n"
            + "<:Moderator:808405808768614460> Riley (<@168531454463049728>)\n"
            + "<:Moderator:808405808768614460> DarkSRC (<@595742728248360960>)\n"
            + "<:Moderator:808405808768614460> IKY (<@564610598248120320>)\n"
            + "<:Moderator:808405808768614460> ThanksDude (<@435314420638416917>)\n"
            + "<:Moderator:808405808768614460> MrMega (<@305805603178020864>)\n",
        )
        await ctx.send(embed=a)

    @gamemoderatorsof.command(name="mcee")
    async def mcee(self, ctx):
        """`Minecraft: Education Edition Game Moderators`"""
        a = discord.Embed(
            colour=discord.Color(0xE41919),
            title="**Minecraft: Education Edition Game Moderators**",
            description="<:SuperMod:808405808793911316> ReniSR (<@577935851154046998>)\n"
            + "<:Moderator:808405808768614460> Insert (<@727035417039339540>)\n"
            + "<:Moderator:808405808768614460> Riley (<@168531454463049728>)\n"
            + "<:Moderator:808405808768614460> picbear (<@675177886096818199>)\n",
        )
        await ctx.send(embed=a)

    @gamemoderatorsof.command(name="mc4k")
    async def mc4k(self, ctx):
        """`Minecraft 4K Game Moderators`"""
        a = discord.Embed(
            colour=discord.Color(0xE41919),
            title="**Minecraft 4K Game Moderators**",
            description="<:SuperMod:808405808793911316> ReniSR (<@577935851154046998>)\n"
            + "<:Moderator:808405808768614460> Insert (<@727035417039339540>)\n"
            + "<:Moderator:808405808768614460> Riley (<@168531454463049728>)\n"
            + "<:Moderator:808405808768614460> markersquire (<@451177399015571457>)\n",
        )
        await ctx.send(embed=a)

    @gamemoderatorsof.command(name="mcpi")
    async def mcpi(self, ctx):
        """`Minecraft: Pi Edition Game Moderators`"""
        a = discord.Embed(
            colour=discord.Color(0xE41919),
            title="**Minecraft: Pi Edition Game Moderators**",
            description="<:SuperMod:808405808793911316> ReniSR (<@577935851154046998>)\n"
            + "<:SuperMod:808405808793911316> Insert (<@727035417039339540>)\n"
            + "<:SuperMod:808405808793911316> Riley (<@168531454463049728>)\n"
            + "<:Moderator:808405808768614460> Quivvy (<@359110554721189889>)\n",
        )
        await ctx.send(embed=a)

    async def subcats(self, subCats: dict, queries: list = None):
        """Get subcategory, from a list."""
        if not queries:
            return []
        queries = [pformat(q) for q in queries]

        res = []
        for data in subCats["data"]:
            if data["is-subcategory"] == False:
                continue
            vals = data["values"]["values"]
            for val in vals.keys():
                if pformat(vals[val]["label"]) in queries:
                    res += [(data["id"], val)]
                    break
        return res

    async def catOrLevel(
        self, game, name=None, levCatName=None, subcats: list = []
    ):
        """Get category/IL (first in the leaderboard or from category's name)."""
        # TODO: Clean this code up!
        cats = game["categories"]
        levels = game["levels"]
        params = ["embed=category,variables,level,game,players"]

        def formatLink(link, params: list):
            return link + "?{}".format(params.pop(0)) + "&{}".format("&".join(params))

        async def getSubCats(variables, subcats, params):
            subcats = await self.subcats(variables, subcats)
            for subcat in subcats:
                params += ["var-{}={}".format(subcat[0], subcat[1])]

        # if levCatName is specificed, most likely its a ILs
        if not levCatName:
            # Get category id
            for cat in cats["data"]:
                if (not name or pformat(cat["name"]) == pformat(name)) and cat[
                    "type"
                ] == "per-game":
                    # If category is the same as input, and is full game cat, return link
                    link = cat["links"][-1]["uri"]
                    await getSubCats(cat["variables"], subcats, params)
                    return formatLink(link, params)
        # Get IL id
        for lev in levels["data"]:
            if not name or pformat(lev["name"]) == pformat(name):
                if not levCatName:
                    # If ILs category name not specified, return the link
                    link = lev["links"][-1]["uri"]
                    await getSubCats(lev["variables"], subcats, params)
                    return formatLink(link, params)
                # handle individual level categories
                for cat in lev["categories"]["data"]:
                    if pformat(cat["name"]) == pformat(levCatName):
                        link = cat["links"][-1]["uri"]
                        await getSubCats(cat["variables"], subcats, params)
                        return formatLink(link, params)

    async def game(self, game: str):
        """Get game data from sr.c"""
        async with self.session.get(
            "{}/games?name={}".format(self.baseUrl, game)
        ) as res:
            _json = json.loads(await res.text())
            try:
                return _json["data"][0]
            except IndexError:
                # Maybe its id after all?
                return game

    @commands.command(
        usage="<game id|name|url> [category|individual level(category)] [subcategories...]",
        aliases=["lb"],
    )
    async def leaderboard(
        self, ctx, game: srcGameLb, category: str = None, *subcategories: str
    ):
        """Gets the leaderboard of a game. Tips: Use "" for name with spaces"""

        e = discord.Embed(
            title="<a:loading:776255339716673566> Loading...",
            colour=discord.Colour.gold(),
        )
        self.initMsg = await ctx.reply(embed=e)

        level = None
        if category:
            regex = self.reLevelAndCat.fullmatch(category)
            if regex:
                regex = regex.groups()
                level = regex[0]
                category = regex[1]

        params = {"game": game, "name": category, "subcats": subcategories}

        if category and level:
            params["name"] = level
            params["levCatName"] = category

        link = await self.catOrLevel(**params)

        async with self.session.get(link) as res:
            lb = json.loads(await res.text())

            if not lb:
                # In case empty lb still happened
                raise srcError.DataNotFound

            pages = MMReplyMenu(
                source=LeaderboardPageSource(ctx, lb), init_msg=self.initMsg, ping=True
            )
            return await pages.start(ctx)

    @leaderboard.error
    async def leaderboard_error(self, ctx, error):
        error = getattr(error, "original", error)
        if isinstance(error, srcError.DataNotFound):
            e = discord.Embed(
                title="<:error:783265883228340245> 404 - No data found",
                colour=discord.Colour.red(),
            )
        else:
            print(error)
            e = discord.Embed(
                title="<:error:783265883228340245> Failed to get data from speedrun.com",
                colour=discord.Colour.red(),
            )
        await self.initMsg.edit(embed=e)

    async def get(self, url):
        async with self.session.get(url) as res:
            return json.loads(await res.text())

    @commands.command(aliases=["uv"], usage="<game id|name|url>")
    async def unverified(self, ctx, *, game: srcGame):
        """Get a game's pending runs count."""
        e = discord.Embed(
            title="<a:loading:776255339716673566> Loading... (SRC API sucks so its going to take a while)",
            colour=discord.Colour.gold(),
        )
        msg = await ctx.reply(embed=e)

        # Loop to get pending runs
        page = 0
        gameData = await self.get(
            "https://www.speedrun.com/api/v1/runs?game={}&status=new&max=200&embed=game&offset={}".format(
                game["id"], page * 200
            )
        )
        while True:
            pagination = gameData["pagination"]["links"]
            if not pagination or "next" not in pagination[-1].values():
                break

            page += 1
            gameData = await self.get(
                "https://www.speedrun.com/api/v1/runs?game={}&status=new&max=200&embed=game&offset={}".format(
                    game["id"], page * 200
                )
            )
        runPending = gameData["pagination"]["size"] + gameData["pagination"]["offset"]

        e = discord.Embed(
            title="{}".format(game["names"]["international"]),
            description="Pending Runs:\n `{}`".format(runPending),
            colour=discord.Colour.gold(),
        )
        e.set_author(
            name="speedrun.com",
            icon_url="https://www.speedrun.com/images/1st.png",
        )
        e.set_thumbnail(
            url=game["assets"]["cover-large"]["uri"],
        )
        await msg.edit(embed=e)

    @commands.command(usage="<game id|name|url>")
    async def categories(self, ctx, game: srcGame):
        """Get the categories of a game"""
        e = discord.Embed(
            title="<a:loading:776255339716673566> Loading...",
            colour=discord.Colour.gold(),
        )
        self.initMsg = await ctx.reply(embed=e)

        data = await self.src.get_games(name=str(game), embeds=["categories.variables"])

        cats = data[0]

        pages = MMReplyMenu(
            source=CategoriesPageSource(ctx, cats),
            init_msg=self.initMsg,
            ping=True,
        )
        return await pages.start(ctx)

    def subcategoryName(self, runVariable, catVariable):
        """Get subcategory name (ex: Set Seed - Random Seed, PC)"""
        subcategoryName = []
        for var in runVariable:
            foundVar = [c for c in catVariable["data"] if c["id"] == var[0]]
            if foundVar and foundVar[0]["is-subcategory"]:
                subcategoryName += [foundVar[0]["values"]["values"][var[1]]["label"]]
        return subcategoryName

    @commands.command(usage="<#channel> <game id|name|url>")
    @commands.has_permissions(manage_messages=True)
    async def pending(self, ctx, channel: discord.TextChannel, game: srcGame):
        """Sends pending runs to a channel"""
        e = discord.Embed(
            title="<a:loading:776255339716673566> Sending pending runs...",
            colour=discord.Colour.gold(),
        )
        self.initMsg = await ctx.reply(embed=e)

        await channel.purge(limit=None)

        offset = 0
        while True:
            async with self.session.get(
                "{}/runs?game={}&status=new&embed=game,players,category.variables,level&max=200&offset={}".format(
                    self.baseUrl, game["id"], offset
                )
            ) as res:
                data = json.loads(await res.text())

            for run in data["data"]:
                gameData = run["game"]["data"]
                levData = run["level"]["data"]
                catData = run["category"]["data"]
                if catData:
                    subcategoryName = self.subcategoryName(
                        run["values"].items(), catData["variables"]
                    )
                if catData["type"] == "per-level":
                    categoryName = (
                        levData["name"]
                        + ": "
                        + catData["name"]
                        + " - "
                        + ", ".join(subcategoryName)
                    )
                else:
                    categoryName = catData["name"]

                players = [
                    player["names"]["international"]
                    if player["rel"] == "user"
                    else player["name"]
                    for player in run["players"]["data"]
                ]
                e = discord.Embed(
                    title="{} by {}".format(
                        realtime(run["times"]["primary_t"]),
                        ",".join(players),
                    ),
                    url=run["weblink"],
                    colour=discord.Colour(0xFFFFF0),
                    timestamp=parser.isoparse(run["date"]),
                )
                e.set_author(
                    name="{} - {}".format(
                        gameData["names"]["international"],
                        categoryName,
                    )
                )
                e.add_field(
                    name="Submitted at",
                    value="`{}`".format(parser.isoparse(run["submitted"])),
                )
                e.set_thumbnail(url=gameData["assets"]["cover-large"]["uri"])

                await channel.send(embed=e)

            pagination = data["pagination"]
            if (
                not pagination["links"]
                or "next" not in pagination["links"][-1].values()
            ):
                runPending = pagination["size"] + pagination["offset"]
                break
            offset += 200

        eTotal = discord.Embed(
            title="Total Runs",
            description="`{}` runs".format(runPending),
            colour=discord.Colour(0xFFFFF0),
        )
        await channel.send(embed=eTotal)

        e = discord.Embed(
            title="Pending runs has been sent",
            colour=discord.Colour.gold(),
        )
        await self.initMsg.edit(embed=e)


def setup(bot):
    bot.add_cog(SRC(bot))
