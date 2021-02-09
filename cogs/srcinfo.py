import discord
from discord.ext import commands

class SRC(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.group(aliases = ['gm'], example=["group"], invoke_without_command=True)
    async def gamemoderatorsof(self, ctx, arg=None):
        """`Figure out who is the Game Moderator of a Game`"""
        embed=discord.Embed(title="<:error:783265883228340245>  **Error!**", description="**Argument (game) not specified. Try using one of these games**", color=0xec0909)
        embed.add_field(name="Minecraft (Classic)", value="mcc", inline=True)
        embed.add_field(name="Classicube", value="cc", inline=True)
        embed.add_field(name="Minecraft: New Nintendo 3DS Edition", value="mc3ds", inline=True)
        embed.add_field(name="Minecraft: Pocket Edition Lite", value="mclite", inline=True)
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
        + "<:Moderator:808405808768614460> NeonTrtl (<@571733724547252227>)\n"
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
        + "<:Moderator:808405808768614460> Kai. (<@447818513906925588>)\n"
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
        + "<:Moderator:808405808768614460> blunderpolicy (<@306969912566611968>)\n"
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
        + "<:Moderator:808405808768614460> MrMega (<@305805603178020864>)\n"
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
        + "<:Moderator:808405808768614460> picbear (<@675177886096818199>)\n"
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
        + "<:Moderator:808405808768614460> markersquire (<@451177399015571457>)\n"
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
        + "<:Moderator:808405808768614460> Quivvy (<@359110554721189889>)\n"
        )
        await ctx.send(embed=a)

def setup(client):
    client.add_cog(SRC(client))
