import discord
from discord.ext import commands

class Insults(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        a = ["nou", "noyou"]
        no_u = ""
        for word in a:
            if word in message.content.lower().replace(" ", ""):
                no_u = "<:ReverseCard:808522739559563285>"
                try:
                    await message.reply(no_u)
                except UnboundLocalError:
                    pass

        b = ["js", "nodejs", "javascript"]
        response = ""
        for word in b:
            if word in message.content.lower().replace(" ", ""):
                response = "Javascript? That hell of a messy code? That is horrible. Make your self a favor and use Python. Thank me later"
                try:
                    await message.reply(response)
                except UnboundLocalError:
                    pass

def setup(client):
    client.add_cog(Insults(client))
