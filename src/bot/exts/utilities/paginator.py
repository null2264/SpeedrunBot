import discord
from discord.ext import menus


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
            self.init_msg = await ctx.reply(embed=e, mention_author=False if not self.ping else True)
        await super().start(ctx)

    async def send_initial_message(self, ctx, channel):
        page = await self._source.get_page(0)
        kwargs = await self._get_kwargs_from_page(page) or {}
        kwargs.pop("mention_author", False)
        await self.init_msg.edit(**kwargs)
        return self.init_msg

    async def _get_kwargs_from_page(self, page):
        no_ping = {"mention_author": False if not self.ping else True}
        value = await discord.utils.maybe_coroutine(self._source.format_page, self, page)
        if isinstance(value, dict):
            return value.update(no_ping)
        elif isinstance(value, str):
            no_ping.update({"content": value})
        elif isinstance(value, discord.Embed):
            no_ping.update({"embed": value})
        return no_ping
