import asyncio
import sys
import traceback

import discord
import pytz
from discord.ext import commands

from .utilities.src import GameNotFound


class ErrorHandler(commands.Cog):
    """Handle errors."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        # This prevents any commands with local handlers being handled here in on_command_error.
        if hasattr(ctx.command, "on_error"):
            return

        # This prevents any cogs with an overwritten cog_command_error being handled here.
        cog = ctx.cog
        if cog:
            if cog._get_overridden_method(cog.cog_command_error) is not None:
                return

        # Allows us to check for original exceptions raised and sent to CommandInvokeError.
        # If nothing is found. We keep the exception passed to on_command_error.
        error = getattr(error, "original", error)

        if isinstance(error, pytz.exceptions.UnknownTimeZoneError):
            ctx.command.reset_cooldown(ctx)
            return await ctx.reply(
                "That's not a valid timezone. You can look them up at https://kevinnovak.github.io/Time-Zone-Picker/"
            )

        if isinstance(error, commands.CommandNotFound):
            return

        if isinstance(error, GameNotFound):
            e = discord.Embed(title=str(error), colour=discord.Colour.red())
            return await ctx.reply(embed=e)

        if isinstance(error, commands.CommandOnCooldown):
            bot_msg = await ctx.send(
                f"{ctx.author.mention}, you have to wait {round(error.retry_after, 2)} seconds before using this again"
            )
            await asyncio.sleep(round(error.retry_after))
            return await bot_msg.delete()

        etype = type(error)
        trace = error.__traceback__
        lines = traceback.format_exception(etype, error, trace)
        print("".join(lines))


async def setup(bot):
    await bot.add_cog(ErrorHandler(bot))
