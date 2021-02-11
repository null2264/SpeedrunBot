import discord
import json
import os
import re
import uuid


from discord.ext import commands
from typing import Union


class Starred:
    __slots__ = ("id", "bot_message_id")

    def __init__(self, message_id: int, bot_message_id: int=None):
        self.id = message_id
        # Return none for Legacy support
        self.bot_message_id = bot_message_id


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


class Stars(commands.Cog):

    STAR_COLOUR = 0xFFAC33

    def __init__(self, bot):
        self.bot = bot
        self.starred = {}

        # Getting starred message from starboard_config.json
        # [TODO] Make it not spaghetti code?
        try:
            with open("starboard_config.json", "r") as conf:
                conf = json.load(conf)
                for guildId in conf:
                    starred = [pin for pin in conf[guildId]["pins"]]
                    for star in starred:
                        try:
                            try:
                                self.starred[guildId] += [Starred(star[0], star[1])]
                            except KeyError:
                                self.starred[guildId] = [Starred(star[0], star[1])]
                        except TypeError:
                            try:
                                self.starred[guildId] += [Starred(star)]
                            except KeyError:
                                self.starred[guildId] = [Starred(star)]
        except FileNotFoundError:
            with open('starboard_config.json', 'w+') as f:
                json.dump({}, f, indent=4)
        self.spoilers = re.compile(r'\|\|(.+?)\|\|')

    def is_mod(ctx):
        try:
            return ctx.author.guild_permissions.manage_channels
        except AttributeError:
            return False

    def get_guild_starboard_config(self, guild_id: str):
        try:
            with open("starboard_config.json", "r") as conf:
                config = json.load(conf)
                return StarboardConfig(guild_id, self.bot, config[str(guild_id)])
        except Exception as err:
            print(err)
            return None
    
    def get_raw_starboard_config(self):
        try:
            with open("starboard_config.json", "r") as conf:
                return json.load(conf)
        except Exception as err:
            print(err)
            return None

    def is_url_spoiler(self, text, url):
        spoilers = self.spoilers.findall(text)
        for spoiler in spoilers:
            if url in spoiler:
                return True
        return False

    @commands.group()
    async def starboard(self, ctx):
        pass

    @starboard.command()
    @commands.check(is_mod)
    async def setup(self, ctx, channel: Union[discord.TextChannel, str] = None, amount: int = 5):
        """`Sets the channel for starboard (Only People with [Administator = True] can use this command)`"""
        if not isinstance(channel, str) and channel.guild.id != ctx.guild.id:
            return

        sbConfig = self.get_raw_starboard_config()

        try:
            guildConfig = sbConfig[str(ctx.guild.id)]
        except KeyError:
            sbConfig[str(ctx.guild.id)] = {}
            guildConfig = sbConfig[str(ctx.guild.id)]
        
        try:
            amount = int(channel) if isinstance(channel, str) else amount
        except ValueError:
            pass
        
        guildConfig["channel"] = channel.id if isinstance(channel, discord.TextChannel) else 0
        guildConfig["amount"] = amount
        if "pins" not in guildConfig:
            guildConfig["pins"] = []

        # Save config to a json file
        self.save_starboard_config(sbConfig)

        channelMentionOrDisabled = channel.mention if isinstance(channel, discord.TextChannel) else "`DISABLED`"

        e = discord.Embed(
            title="Starboard Setup",
            description="Channel: {}\nRequired stars: `{}`".format(
                channelMentionOrDisabled,
                amount
            ),
            colour=discord.Colour(self.STAR_COLOUR),
        )

        await ctx.send(embed=e)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if str(payload.emoji) != "⭐":
            return

        starboard = self.get_guild_starboard_config(payload.guild_id)
        if not starboard:
            return
        
        if not starboard.channel:
            return

        msg_id = payload.message_id

        def isStarred():
            if str(payload.guild_id) not in self.starred:
                return False

            for star in self.starred[str(payload.guild_id)]:
                if msg_id == star.id or msg_id == star.bot_message_id:
                    return True
            return False

        if not isStarred():
            ch = self.bot.get_channel(payload.channel_id)
            msg = await ch.fetch_message(msg_id)
            count = sum([reaction.count for reaction in msg.reactions if str(reaction) == "⭐"])
            if count >= starboard.amount:
                await self.star_message(starboard.channel, msg)

    def save_starboard_config(self, data):
        temp = '{}-{}.tmp'.format(uuid.uuid4(), "starboard_config.json")
        with open(temp, "w") as tmp:
            json.dump(data.copy(), tmp, indent=4)

        os.replace(temp, "starboard_config.json")

    async def star_message(self, channel, message):
        e = discord.Embed(
            title="New starred message!",
            description=message.content,
            colour=discord.Colour(self.STAR_COLOUR),
            timestamp=message.created_at,
        )

        if message.embeds:
            embed = message.embeds[0]
            if embed.type == "rich":
                e.add_field(
                    name="[{}]".format(
                        embed.title if str(embed.title) != "Embed.Empty" else "\u200B"
                    ),
                    value=embed.description or "\u200B", inline=False
                )
                for field in embed.fields:
                    e.add_field(name=field.name, value=field.value, inline=field.inline)
            if embed.type == 'image' and not self.is_url_spoiler(message.content, embed.url):
                e.set_image(url=embed.url)

        if message.attachments:
            file = message.attachments[0]
            spoiler = file.is_spoiler()
            if not spoiler and file.url.lower().endswith(('png', 'jpeg', 'jpg', 'gif', 'webp')):
                e.set_image(url=file.url)
            elif spoiler:
                e.add_field(name='Attachment', value=f'||[{file.filename}]({file.url})||', inline=False)
            else:
                e.add_field(name='Attachment', value=f'[{file.filename}]({file.url})', inline=False)

        e.add_field(name="Original", value=f"[Jump!]({message.jump_url})", inline=False)
        e.set_author(name=message.author, icon_url=message.author.avatar_url)
        e.set_footer(text="ID: {}".format(message.id))
        bot_msg = await channel.send(embed=e)

        with open("starboard_config.json", "r") as cur:
            cur = json.load(cur)

        try:
            self.starred[str(message.guild.id)] += [Starred(message.id, bot_msg.id)]
        except KeyError:
            self.starred[str(message.guild.id)] = [Starred(message.id, bot_msg.id)]

        # Save starred message to a json file
        cur[str(message.guild.id)]["pins"] = [(star.id, star.bot_message_id) for star in self.starred[str(message.guild.id)]]
        self.save_starboard_config(cur)


def setup(bot):
    bot.add_cog(Stars(bot))
