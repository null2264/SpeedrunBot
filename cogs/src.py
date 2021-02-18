import discord


from discord.ext import commands
from speedrunpy import SpeedrunPy


class SRC(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.src = SpeedrunPy()

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


def setup(client):
    client.add_cog(SRC(client))
