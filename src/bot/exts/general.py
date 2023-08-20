import datetime
import random
import re
import time
from random import randint

import discord
from discord.errors import Forbidden
from discord.ext import commands
from pytz import timezone


class MyHelpCommand(commands.MinimalHelpCommand):
    messages = [
        "I actually don't like mangoes",
    ]

    def get_command_signature(self, command):
        return f"``{self.context.clean_prefix}{command.qualified_name} {command.signature}``"

    def get_ending_note(self) -> str:
        return self.messages[randint(0, len(self.messages) - 1)]


class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._original_help_command = bot.help_command
        bot.help_command = MyHelpCommand()
        bot.help_command.cog = self

    def cog_unload(self):
        self.bot.help_command = self._original_help_command

    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        print("Bot is Online!")

    # Commands
    @commands.command()
    async def ping(self, ctx, arg=None):
        """`Checks Bots Ping`"""
        if arg == "pong":
            return await ctx.send("Congratulations, you just ponged yourself lol")

        else:
            start = time.perf_counter()
            message = await ctx.send("Ping...")
            end = time.perf_counter()
            duration = (end - start) * 1000
            await message.edit(content="Pong! {:.2f}ms".format(duration))

    @commands.command(
        aliases=[
            "bi",
            "about",
            "info",
        ]
    )
    async def botinfo(self, ctx):
        """`Show the bot's information.`"""
        bot_ver = "1.0.A"
        embed = discord.Embed(
            title="Mango Man Bot",
            colour=discord.Colour(0xFFFFF0),
            timestamp=ctx.message.created_at,
        )
        embed.set_thumbnail(url=self.bot.user.avatar_url)
        embed.add_field(
            name="Mango Man Bot Team",
            value="<@564610598248120320>, and <@186713080841895936>",
        )
        embed.add_field(
            name="discord.py",
            value=f"[{discord.__version__}](https://github.com/Rapptz/discord.py)",
        )
        embed.add_field(
            name="About",
            value="**Mango Man Bot** is an [open source bot](https://github.com/null2264/Mango-Man-Bot), "
            + "a fork of [IKY's Bot](https://github.com/AnInternetTroll/mcbeDiscordBot) "
            + "(InKY Bot) created by [xIKYx](https://github.com/xIKYx) "
            + f"but rewritten a bit.\n\n**Bot Version**: {bot_ver}",
            inline=False,
        )
        embed.set_footer(text=f"Requested by {ctx.message.author.name}#{ctx.message.author.discriminator}")
        await ctx.send(embed=embed)

    @commands.command(name="source")
    async def _source(self, ctx):
        """`Gives my source code repository`"""
        await ctx.send("My source code repository: https://github.com/null2264/Mango-Man-Bot")

    @commands.command(aliases=["ui"], usage="[member]")
    async def userinfo(self, ctx, *, user: discord.Member = None):
        """`Shows user information.`"""
        member = user or ctx.message.author

        def stat(x):
            return {
                "offline": "<:status_offline:747799247243575469>",
                "idle": "<:status_idle:747799258316668948>",
                "dnd": "<:status_dnd:747799292592259204>",
                "online": "<:status_online:747799234828435587>",
                "streaming": "<:status_streaming:747799228054765599>",
            }.get(str(x), "None")

        def badge(x):
            return {
                "UserFlags.hypesquad_balance": "<:balance:747802468586356736>",
                "UserFlags.hypesquad_brilliance": "<:brilliance:747802490241810443>",
                "UserFlags.hypesquad_bravery": "<:bravery:747802479533490238>",
                "UserFlags.bug_hunter": "<:bughunter:747802510663745628>",
                "UserFlags.booster": "<:booster:747802502677659668>",
                "UserFlags.hypesquad": "<:hypesquad:747802519085776917>",
                "UserFlags.partner": "<:partner:747802528594526218>",
                "UserFlags.owner": "<:owner:747802537402564758>",
                "UserFlags.staff": "<:stafftools:747802548391379064>",
                "UserFlags.early_supporter": "<:earlysupport:747802555689730150>",
                "UserFlags.verified": "<:verified:747802457798869084>",
                "UserFlags.verified_bot": "<:verified:747802457798869084>",
                "UserFlags.verified_bot_developer": "<:verified_bot_developer:748090768237002792>",
            }.get(x, "🚫")

        def activity(x):
            return {
                "playing": "Playing ",
                "watching": "Watching ",
                "listening": "Listening to ",
                "streaming": "Streaming ",
                "custom": "",
            }.get(x, "None ")

        badges = []
        for x in list(member.public_flags.all()):
            x = str(x)
            if member == ctx.guild.owner:
                badges.append(badge("UserFlags.owner"))
            badges.append(badge(x))

        roles = []
        if member:
            for role in member.roles:
                if role.name != "@everyone":
                    roles.append(role.mention)

        if member:
            status = member.status
            statEmoji = stat(member.status)
        else:
            status = "Unknown"
            statEmoji = "❓"
        embed = discord.Embed(
            description=f"{statEmoji}({status})\n"
            + (
                "<:activity:748091280227041281>"
                + activity(str(member.activity.type).replace("ActivityType.", ""))
                + f"**{member.activity.name}**"
                if member and member.activity
                else ""
            ),
            colour=member.colour if member else discord.Colour(0x000000),
            timestamp=ctx.message.created_at,
        )
        embed.set_author(name=f"{member}", icon_url=member.avatar_url)
        embed.set_thumbnail(url=member.avatar_url)
        embed.add_field(name="ID", value=member.id)
        embed.add_field(name="Guild name", value=member.display_name)
        embed.add_field(name="Badges", value=" ".join(badges) if badges else "No badge.")
        embed.add_field(
            name="Created on",
            value=member.created_at.replace(tzinfo=timezone("UTC")).strftime("%a, %#d %B %Y, %H:%M"),
        )
        embed.add_field(
            name="Joined on",
            value=member.joined_at.replace(tzinfo=timezone("UTC")).strftime("%a, %#d %B %Y, %H:%M")
            if member
            else "Not a member.",
        )
        if len(", ".join(roles)) <= 1024:
            embed.add_field(
                name=f"Roles ({len(roles)})",
                value=", ".join(roles) or "No roles.",
                inline=False,
            )
        else:
            embed.add_field(name=f"Roles", value=f"{len(roles)}", inline=False)
        embed.set_footer(text=f"Requested by {ctx.message.author.name}#{ctx.message.author.discriminator}")
        await ctx.send(embed=embed)

    @commands.command(aliases=["si"])
    async def serverinfo(self, ctx):
        """`Show server information.`"""
        embed = discord.Embed(
            title=f"About {ctx.guild.name}",
            colour=discord.Colour(0xFFFFF0),
            timestamp=ctx.message.created_at,
        )

        roles = []
        for role in ctx.guild.roles:
            if role.name != "@everyone":
                roles.append(role.mention)
        width = 3

        boosters = [x.mention for x in ctx.guild.premium_subscribers]

        embed.add_field(name="Owner", value=f"{ctx.guild.owner.mention}", inline=False)
        embed.add_field(name="Created on", value=f"{ctx.guild.created_at.date()}")
        embed.add_field(name="Region", value=f"``{ctx.guild.region}``")
        embed.set_thumbnail(url=ctx.guild.icon_url)
        embed.add_field(name="Verification Level", value=f"{ctx.guild.verification_level}".title())
        embed.add_field(
            name="Channels",
            value="<:categories:747750884577902653>"
            + f" {len(ctx.guild.categories)}\n"
            + "<:text_channel:747744994101690408>"
            + f" {len(ctx.guild.text_channels)}\n"
            + "<:voice_channel:747745006697185333>"
            + f" {len(ctx.guild.voice_channels)}",
        )
        embed.add_field(name="Members", value=f"{ctx.guild.member_count}")
        if len(boosters) < 5:
            embed.add_field(
                name=f"Boosters ({len(boosters)})",
                value=",\n".join(", ".join(boosters[i : i + width]) for i in range(0, len(boosters), width))
                if boosters
                else "No booster.",
            )
        else:
            embed.add_field(name=f"Boosters ({len(boosters)})", value=len(boosters))
        if len(", ".join(roles)) <= 1024:
            embed.add_field(name=f"Roles ({len(roles)})", value=", ".join(roles))
        else:
            embed.add_field(name=f"Roles", value=f"{len(roles)}")
        embed.set_footer(text=f"ID: {ctx.guild.id}")
        await ctx.send(embed=embed)

    @commands.command(aliases=["ei"])
    async def emojiinfo(self, ctx, *, emojiname: str):
        """Displays Emoji Information"""
        emojiname = emojiname.replace(" ", "_")
        match = re.findall(r"\b(?<!<)\w+\b", emojiname, re.I)
        emojiname = match[0].lower()
        for emoji_type in self.bot.emojis:
            emoji_name = emoji_type.name.lower()
            if emoji_name == emojiname:
                emoji = emoji_type
                break
        embed = discord.Embed(
            title="Emoji information",
            colour=0xFF00FF,
            timestamp=datetime.datetime.utcnow(),
        )
        embed.set_thumbnail(url=emoji.url)
        fields = [
            ("Name", emoji.name, True),
            ("Emoji Preview", (emoji), True),
            ("ID", emoji.id, True),
            ("Created by", (f"{emoji.user}"), True),
            ("Created at", emoji.created_at.strftime("%d/%m/%Y %H:%M:%S"), True),
            ("Emoji Url", emoji.url, True),
            ("Emoji Guild Name", emoji.guild, True),
            ("Emoji Guild ID", emoji.guild_id, True),
            ("Bot String", f"`{emoji}`", True),
            ("Is Animated?", emoji.animated, True),
            ("Is Restricted?", len(emoji.roles), True),
            ("Can Bot use It?", emoji.is_usable(), True),
            ("Is Available?", emoji.available, True),
            ("Is Managed by Twitch?", emoji.managed, True),
        ]
        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)
        await ctx.send(embed=embed)

    @commands.command(aliases=["sug"])
    async def suggestion(self, ctx, *, suggestion):
        """`Give suggestions to add to the bot!`"""

        owners = (
            564610598248120320,
            186713080841895936,
        )
        owners = [self.bot.get_user(id) for id in owners]

        if suggestion == None:
            await ctx.send("Please type a suggjestion to suggest smhmyhead")

        else:
            for bot_owner in owners:
                await bot_owner.send(f"{ctx.author} has suggested {suggestion}")
            await ctx.send("Thank for your suggestion. The owner will review your suggestion")

    @commands.command()
    async def welcome(self, ctx):
        await ctx.send("Welcome! :]")


async def setup(bot):
    await bot.add_cog(General(bot))
