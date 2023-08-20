from __future__ import annotations

import re
from typing import TYPE_CHECKING, Union

import discord
from discord.ext import commands

from ..core import db

if TYPE_CHECKING:
    from ..core.bot import MangoManBot


SPOILERS = re.compile(r"\|\|(.+?)\|\|")


class Starred:
    __slots__ = ("id", "bot_message_id")

    def __init__(self, message_id: int, bot_message_id: int = None):
        self.id = message_id
        # Return none for Legacy support
        self.bot_message_id = bot_message_id

    def __repr__(self):
        return "<Starred: {}, {}>".format(self.id, self.bot_message_id)


class StarboardConfig:
    __slots__ = ("id", "bot", "channel_id", "amount")

    def __init__(self, guild_id: str, bot, config=None):
        self.id = guild_id
        self.bot = bot
        if config:
            self.channel_id = config["channel"]
            self.amount = config["amount"]

    @property
    def channel(self):
        ch = self.bot.get_channel(self.channel_id)
        return ch


def is_mod(ctx):
    try:
        return ctx.author.guild_permissions.manage_channels
    except AttributeError:
        return False


STAR_COLOUR = 0xFFAC33


class Stars(commands.Cog):

    def __init__(self, bot):
        self.bot: MangoManBot = bot

    async def get_guild_starboard_config(self, guild_id: int) -> db.Starboard | None:
        try:
            return await db.Starboard.async_get(guild_id=guild_id)
        except db.Starboard.DoesNotExist:
            return None

    def is_url_spoiler(self, text, url):
        spoilers = SPOILERS.findall(text)
        for spoiler in spoilers:
            if url in spoiler:
                return True
        return False

    @commands.group()
    async def starboard(self, _):
        pass

    @starboard.command()
    @commands.check(is_mod)
    async def setup(self, ctx, channel: Union[discord.TextChannel, str] = None, amount: int = 5):
        """`Sets the channel for starboard (Only People with [Administator = True] can use this command)`"""
        if not channel:
            return

        if not isinstance(channel, str) and channel.guild.id != ctx.guild.id:
            return

        try:
            amount = int(channel) if isinstance(channel, str) else amount
        except ValueError:
            pass

        channel_id: int | None = channel.id if isinstance(channel, discord.TextChannel) else None
        if not channel_id:
            starboard = await self.get_guild_starboard_config(ctx.guild.id)
            if not starboard:
                return await ctx.send("Starboard channel is not yet set, please set the channel first!\nE.g. `mm!starboard setup #channel`")
            await starboard.async_update(amount=amount)
        else:
            await db.Starboard.async_create(id=channel_id, guild_id=ctx.guild.id, amount=amount)

        channelMentionOrDisabled = channel.mention if isinstance(channel, discord.TextChannel) else "`DISABLED`"

        e = discord.Embed(
            title="Starboard Setup",
            description="Channel: {}\nRequired stars: `{}`".format(channelMentionOrDisabled, amount),
            colour=discord.Colour(STAR_COLOUR),
        )

        await ctx.send(embed=e)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if str(payload.emoji) != "⭐":
            return

        starboard = await self.get_guild_starboard_config(payload.guild_id)
        if not starboard:
            return

        starboard_ch = self.bot.get_channel(starboard.id)  # type: ignore
        if not starboard_ch:
            return

        msg_id = payload.message_id

        async def is_starred():
            try:
                await db.Starred.async_get(guild_id=payload.guild_id, id=msg_id, bot_message_id=msg_id)
                return True
            except db.Starred.DoesNotExist:
                return False

        if not await is_starred():
            # Get message from cache
            msg = discord.utils.get(self.bot.cached_messages, id=msg_id)
            # If not found, get message from discord
            if not msg:
                ch = self.bot.get_channel(payload.channel_id)
                if not ch:
                    return
                if isinstance(ch, (discord.ForumChannel, discord.CategoryChannel, discord.abc.PrivateChannel)):
                    return  # invalid channel
                msg = await ch.fetch_message(msg_id)

            count = sum([reaction.count for reaction in msg.reactions if str(reaction) == "⭐"])
            if count >= starboard.amount:
                await self.star_message(starboard_ch, msg)

    async def star_message(self, channel, message):
        e = discord.Embed(
            title="New starred message!",
            description=message.content,
            colour=discord.Colour(STAR_COLOUR),
            timestamp=message.created_at,
        )

        if message.embeds:
            embed = message.embeds[0]
            if embed.type == "rich":
                e.add_field(
                    name="[{}]".format(embed.title if str(embed.title) != "Embed.Empty" else "\u200B"),
                    value=embed.description or "\u200B",
                    inline=False,
                )
                for field in embed.fields:
                    e.add_field(name=field.name, value=field.value, inline=field.inline)
            if embed.type == "image" and not self.is_url_spoiler(message.content, embed.url):
                e.set_image(url=embed.url)

        if message.attachments:
            file = message.attachments[0]
            spoiler = file.is_spoiler()
            if not spoiler and file.url.lower().endswith(("png", "jpeg", "jpg", "gif", "webp")):
                e.set_image(url=file.url)
            elif spoiler:
                e.add_field(
                    name="Attachment",
                    value=f"||[{file.filename}]({file.url})||",
                    inline=False,
                )
            else:
                e.add_field(
                    name="Attachment",
                    value=f"[{file.filename}]({file.url})",
                    inline=False,
                )

        e.add_field(name="Original", value=f"[Jump!]({message.jump_url})", inline=False)
        e.set_author(name=message.author, icon_url=message.author.avatar_url)
        e.set_footer(text="ID: {}".format(message.id))
        bot_msg = await channel.send(embed=e)

        await db.Starred.async_create(type=1, id=message.id, guild_id=message.guild.id, bot_message_id=bot_msg.id)


async def setup(bot):
    await bot.add_cog(Stars(bot))
