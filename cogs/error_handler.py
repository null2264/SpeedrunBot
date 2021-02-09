import asyncio
import discord
import json
import sys
import traceback


from discord.ext import commands


class ErrorHandler(commands.Cog):
    """Handle errors."""

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return

        if isinstance(error, commands.CommandOnCooldown):
            bot_msg = await ctx.send(
                f"{ctx.author.mention}, you have to wait {round(error.retry_after, 2)} seconds before using this again"
            )
            await asyncio.sleep(round(error.retry_after))
            await bot_msg.delete()
            return

def setup(client):
    client.add_cog(ErrorHandler(client))