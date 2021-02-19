import aiohttp
import discord
import json
import re


from .utilities.formatting import realtime, pformat
from discord.ext import commands, menus
from speedrunpy import SpeedrunPy, errors as srcError


class MMMenu(menus.MenuPages):
    def __init__(self, source, init_msg=None, check_embeds=True, ping=False, loop=None):
        super().__init__(source=source, check_embeds=check_embeds)
        self.ping = ping
        self.init_msg = init_msg

    async def start(self, ctx):
        if not self.init_msg:
            e = discord.Embed(title="Loading...", colour=discord.Colour.blue())
            self.init_msg = await ctx.channel.send(embed=e)
        await super().start(ctx)

    async def send_initial_message(self, ctx, channel):
        page = await self._source.get_page(0)
        kwargs = await self._get_kwargs_from_page(page)
        if self.init_msg:
            await self.init_msg.edit(**kwargs)
            return self.init_msg

    async def update(self, payload):
        if self._can_remove_reactions:
            if payload.event_type == "REACTION_ADD":
                channel = self.bot.get_channel(payload.channel_id)
                msg = channel.get_partial_message(payload.message_id)
                await msg.remove_reaction(payload.emoji, payload.member)
            elif payload.event_type == "REACTION_REMOVE":
                return
        await super().update(payload)

    async def finalize(self, timed_out):
        try:
            if timed_out:
                await self.message.clear_reactions()
            else:
                await self.message.delete()
        except discord.HTTPException:
            pass


class MMReplyMenu(MMMenu):
    def __init__(self, source, ping=False, **kwargs):
        self.ping = ping
        super().__init__(source=source, check_embeds=True, **kwargs)

    async def start(self, ctx):
        if not self.init_msg:
            e = discord.Embed(title="Loading...", colour=discord.Colour.blue())
            self.init_msg = await ctx.reply(
                embed=e, mention_author=False if not self.ping else True
            )
        await super().start(ctx)

    async def send_initial_message(self, ctx, channel):
        page = await self._source.get_page(0)
        kwargs = await self._get_kwargs_from_page(page)
        await self.init_msg.edit(**kwargs)
        return self.init_msg

    async def _get_kwargs_from_page(self, page):
        no_ping = {"mention_author": False if not self.ping else True}
        value = await discord.utils.maybe_coroutine(
            self._source.format_page, self, page
        )
        if isinstance(value, dict):
            return value.update(no_ping)
        elif isinstance(value, str):
            no_ping.update({"content": value})
        elif isinstance(value, discord.Embed):
            no_ping.update({"embed": value})
        return no_ping


class LeaderboardPageSource(menus.ListPageSource):
    def __init__(self, ctx, data):
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
                    self.varName += [variable["values"]["values"][self.data["values"][value]]["label"]]

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
        e.set_footer(text="Requested by {}".format(str(self.ctx.author)), icon_url=self.ctx.author.avatar_url)

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
    def __init__(self, client):
        self.client = client
        self.session = aiohttp.ClientSession()
        self.src = SpeedrunPy(session=self.session)
        self.reLevelAndCat = re.compile(r"(.*)\((.*)\)")


    @commands.command(aliases=["v"])
    async def verified(self, ctx, user: str, game: str = None):
        """Get how many run a user have verified."""
        e = discord.Embed(
            title="<a:loading:776255339716673566> Loading... (SRC API sucks so its going to take a while)",
            colour=discord.Colour.gold(),
        )
        msg = await ctx.reply(embed=e)

        # Get user data
        userData = await self.src.get("/users", "?lookup={}".format(user))
        if "status" in userData or not userData["data"]:
            # User not found
            e = discord.Embed(
                title="<:error:783265883228340245> 404 - User not found!",
                colour=discord.Colour.red(),
            )
            return await msg.edit(embed=e)
        userID = userData["data"][0]["id"]
        userName = userData["data"][0]["names"]["international"]

        params = {"examiner": userID, "page": 0, "perPage": 200}
        if game:
            # Get game id if game is specified
            games = await self.src.get_games(name=game)
            params["game"] = games[0].id

        # Loop to get verified runs
        runs = await self.src.get_runs(**params)
        while runs.hasNextPage is True:
            params["page"] += 1
            runs = await self.src.get_runs(**params)
        runVerified = runs.size + runs.offset

        e = discord.Embed(
            title="{}".format(userName),
            description="Runs verified:\n `{}`".format(runVerified),
            colour=discord.Colour.gold(),
        )
        e.set_thumbnail(
            url="https://www.speedrun.com/themes/user/{}/image.png".format(userName)
        )
        await msg.edit(embed=e)

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
        msg = await ctx.send("Loading...")
        data = await self.src.get("/users", "/{}/personal-bests".format(user))
        try:
            data = data["data"]
        except KeyError:
            return await ctx.send(f"There's no user called `{user}`")
        fullgame_wr = sum([1 for pb in data if pb["place"] == 1 and not pb["run"]["level"]])
        ils_wr = sum([1 for pb in data if pb["place"] == 1 and pb["run"]["level"]])
        # for pb in data:
        #     if pb["place"] > 1:
        #         continue

        #     if pb["run"]["level"]:
        #         ils_wr += 1
        #     elif not pb["run"]["level"]:
        #         fullgame_wr += 1
        #     else:
        #         # Uh oh!
        #         continue
        await msg.edit(content=
            "{} has ".format(await self.username(await self.get_user_id(user)))
            + f"**{fullgame_wr + ils_wr}** world records:\n**{fullgame_wr}** full game "
            + f"record{'s' if fullgame_wr > 1 else ''} and "
            + f"**{ils_wr}** IL record{'s' if ils_wr > 1 else ''}"
        )

    @commands.group(aliases=["gm"], example=["group"], invoke_without_command=True)
    async def gamemoderatorsof(self, ctx, arg=None):
        """`Figure out who is the Game Moderator of a Game`"""
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

    async def subcats(self, _type: str, category: str, queries: list=None):
        """Get subcategory, from a list."""
        if not queries:
            return []
        queries = [pformat(q) for q in queries]
        
        res = []
        subCats = await self.src.get("/{}/".format(_type), "{}/variables".format(category))
        for data in subCats["data"]:
            if data["is-subcategory"] == False:
                continue
            vals = data["values"]["values"]
            for val in vals.keys():
                if pformat(vals[val]["label"]) in queries:
                    res += [(data["id"], val)]
                    break
        return res

    async def catOrLevel(self, game: str, name=None, levCatName=None, subcats: list=[]):
        """Get category/IL (first in the leaderboard or from category's name)."""
        # TODO: Clean this code up!
        cats = await self.src.get_categories(game=game)
        levels = await self.src.get("/games/", "{}/levels".format(game))
        params = ["embed=category,variables,level,game,players"]

        def formatLink(link, params: list):
            return link + "?{}".format(params.pop(0)) + "&{}".format("&".join(params))

        async def getSubCats(_type, catId, subcats, params):
            subcats = await self.subcats(_type, catId, subcats)
            for subcat in subcats:
                params += ["var-{}={}".format(subcat[0], subcat[1])]

        # if category name specified
        if name:
            if not levCatName:
                # Get category id
                for cat in cats:
                    if pformat(cat.name) == pformat(name):
                        if cat.type == "per-game":
                            # If category is the same as input, and is full game cat, return link
                            link = cat.rawData["links"][-1]["uri"]
                            await getSubCats("categories", cat.id, subcats, params)
                            return formatLink(link, params) 
            # Get IL id
            for lev in levels["data"]:
                if pformat(lev["name"]) == pformat(name):
                    if not levCatName:
                        # If ILs category name not specified, return the link
                        link = lev["links"][-1]["uri"]
                        await getSubCats("levels", lev["id"], subcats, params)
                        return formatLink(link, params) 
                    levCats = await self.src.get("/levels/", "{}/categories".format(lev["id"]))
                    for cat in levCats["data"]:
                        if pformat(cat["name"]) == pformat(levCatName):
                            link = cat["links"][-1]["uri"]
                            await getSubCats("categories", cat["id"], subcats, params)
                            return formatLink(link, params) 

        # if name is None:
        if cats[0].type == "per-game":
            link = cats[0].rawData["links"][-1]["uri"]
            await getSubCats("categories", cats[0].id, subcats, params)
            return formatLink(link, params) 
        # if ILs:
        link = levels["data"][0]["links"][-1]["uri"]
        await getSubCats("levels", levels["data"][0]["id"], subcats, params)
        return formatLink(link, params) 

    @commands.command(usage="<game> [category|individual level(category)] [subcategories...]", aliases=["lb"])
    async def leaderboard(self, ctx, game: str, category: str = None, *subcategories: str):
        """Get leaderboard of a game. Tips: Use "" for name with spaces"""
        
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
                source=LeaderboardPageSource(ctx, lb),
                init_msg=self.initMsg,
                ping=True
            )
            return await pages.start(ctx)
    
    @leaderboard.error
    async def leaderboard_error(self, ctx, error):
        error = getattr(error, 'original', error)
        if isinstance(error, srcError.DataNotFound):
            e = discord.Embed(
                title="<:error:783265883228340245> 404 - No data found",
                colour=discord.Colour.red(),
            )
        else:
            e = discord.Embed(
                title="<:error:783265883228340245> Failed to get data from speedrun.com",
                colour=discord.Colour.red(),
            )
        await self.initMsg.edit(embed=e)


def setup(client):
    client.add_cog(SRC(client))
