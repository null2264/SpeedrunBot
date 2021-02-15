import discord
import asyncio
import json
import requests

from discord.errors import Forbidden
from discord.ext import commands
from random import choice, randint, random
from .utilities.barter import Piglin

class Fun(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.pins = []
    
    # Commands
    @commands.cooldown(1, 30, commands.BucketType.guild)
    @commands.command(aliases=["fs"])
    async def findseed(self, ctx):
        """`Test your Minecraft RNG, but in a bot command`"""
        total_eyes = sum([1 for i in range(12) if randint(1, 10) == 1])
        await ctx.send(
            f"{(ctx.message.author.mention)} -> your seed is a {total_eyes} eye"
        )

    @commands.cooldown(1, 30, commands.BucketType.guild)    
    @commands.command(aliases=["vfindseed", "visualfindseed", "vfs"])
    async def findseedbutvisual(self, ctx):
        """`Test your Minecraft RNG, but you can physaclly see it`"""
        emojis = {
            "{air}": "<:empty:754550188269633556>",
            "{frame}": "<:portal:754550231017979995>",
            "{eye}": "<:eye:754550267382333441>",
        }

        eyes = ["{eye}" if randint(1, 10) == 1 else "{frame}" for i in range(12)]
        sel_eye = 0
        portalframe = ""
        for row in range(5):
            for col in range(5):
                if ((col == 0 or col == 4) and (row != 0 and row != 4)) or (
                    (row == 0 or row == 4) and (col > 0 and col < 4)
                ):
                    sel_eye += 1
                    portalframe += eyes[sel_eye - 1]
                else:
                    portalframe += "{air}"
            portalframe += "\n"

        # replace placeholder with portal frame emoji
        for placeholder in emojis.keys():
            portalframe = portalframe.replace(placeholder, emojis[placeholder])

        e = discord.Embed(
            title="findseed but visual",
            description=f"Your seed looks like: \n\n{portalframe}",
            color=discord.Colour(0x38665E),
        )
        e.set_author(
            name=f"{ctx.message.author.name}#{ctx.message.author.discriminator}",
            icon_url=ctx.message.author.avatar_url,
        )
        await ctx.send(embed=e)

    @commands.cooldown(1, 30, commands.BucketType.guild)
    @commands.command(aliases=["vfsbp"])
    async def findseedbutvisualbutpipega(self, ctx):
        """`Test your Minecraft RNG, but you can physaclly see it, and its pipega.`"""
        emojis = {
            "{air}": "<:empty:754550188269633556>",
            "{frame}": "<:piog:797563853902446592>",
            "{eye}": "<:pepiga:797563870793039873>",
        }

        eyes = ["{eye}" if randint(1, 10) == 1 else "{frame}" for i in range(12)]
        sel_eye = 0
        portalframe = ""
        for row in range(5):
            for col in range(5):
                if ((col == 0 or col == 4) and (row != 0 and row != 4)) or (
                    (row == 0 or row == 4) and (col > 0 and col < 4)
                ):
                    sel_eye += 1
                    portalframe += eyes[sel_eye - 1]
                else:
                    portalframe += "{air}"
            portalframe += "\n"

        # replace placeholder with portal frame emoji
        for placeholder in emojis.keys():
            portalframe = portalframe.replace(placeholder, emojis[placeholder])

        e = discord.Embed(
            title="findseed but visual",
            description=f"Your seed looks like: \n\n{portalframe}",
            color=discord.Colour(0xF4ABBA),
        )
        e.set_author(
            name=f"{ctx.message.author.name}#{ctx.message.author.discriminator}",
            icon_url=ctx.message.author.avatar_url,
        )
        await ctx.send(embed=e)

    @commands.cooldown(1, 30, commands.BucketType.guild)
    @commands.command(aliases=["vfsbpog"])
    async def findseedbutvisualbutpog(self, ctx):
        """`Test your Minecraft RNG, but you can physaclly see it,and its pog.`"""
        emojis = {
            "{air}": "<:empty:754550188269633556>",
            "{frame}": "<:pog:798221486803779584>",
            "{eye}": "<:pogmouth:798224025272844288>",
        }

        eyes = ["{eye}" if randint(1, 10) == 1 else "{frame}" for i in range(12)]
        sel_eye = 0
        portalframe = ""
        for row in range(5):
            for col in range(5):
                if ((col == 0 or col == 4) and (row != 0 and row != 4)) or (
                    (row == 0 or row == 4) and (col > 0 and col < 4)
                ):
                    sel_eye += 1
                    portalframe += eyes[sel_eye - 1]
                else:
                    portalframe += "{air}"
            portalframe += "\n"

        # replace placeholder with portal frame emoji
        for placeholder in emojis.keys():
            portalframe = portalframe.replace(placeholder, emojis[placeholder])

        e = discord.Embed(
            title="findseed but visual",
            description=f"Your seed looks like: \n\n{portalframe}",
            color=discord.Colour(0xD78369),
        )
        e.set_author(
            name=f"{ctx.message.author.name}#{ctx.message.author.discriminator}",
            icon_url=ctx.message.author.avatar_url,
        )
        await ctx.send(embed=e)

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command()
    async def flip(self, ctx):
        """`Flip a coin, thats it`"""
        await ctx.send(f"You got {choice(['heads', 'tails'])}!")

    @commands.cooldown(1, 30, commands.BucketType.user)
    @commands.command(
        usage="(choice)",
        brief="`The Classic Paper Rock Sccicors game, but with no friends, instead its with the bot`",
        example="{prefix}rps rock",
    )
    async def rps(self, ctx, choice: str):
        choice = choice.lower()
        rps = ["rock", "paper", "scissors"]
        bot_choice = rps[randint(0, len(rps) - 1)]

        await ctx.send(
            f"You chose ***{choice.capitalize()}***."
            + f" I chose ***{bot_choice.capitalize()}***."
        )
        if bot_choice == choice:
            await ctx.send("It's a Tie!")
        elif bot_choice == rps[0]:

            def f(x):
                return {"paper": "Paper wins!", "scissors": "Rock wins!"}.get(
                    x, "Rock wins!"
                )

            result = f(choice)
        elif bot_choice == rps[1]:

            def f(x):
                return {"rock": "Paper wins!", "scissors": "Scissors wins!"}.get(
                    x, "Paper wins!"
                )

            result = f(choice)
        elif bot_choice == rps[2]:

            def f(x):
                return {"paper": "Scissors wins!", "rock": "Rock wins!"}.get(
                    x, "Scissors wins!"
                )

            result = f(choice)
        else:
            return
        if choice == "noob":
            result = "Noob wins!"
        await ctx.send(result)

    @commands.cooldown(1, 30, commands.BucketType.guild)
    @commands.command()
    async def findsleep(self, ctx):
        """`See how long you sleep, this is 100% true I swear`"""

        lessSleepMsg = [
            "gn, insomniac!",
            "counting sheep didn't work? try counting chloroform vials!",
            "try a glass of water",
            "some decaf coffee might do the trick!",
        ]

        moreSleepMsg = [
            "waaakeee uuuppp!",
            "are they dead or asleep? I can't tell.",
            "wake up, muffin head",
            "psst... coffeeee \\:D",
        ]

        sleepHrs = randint(0, 24)

        if sleepHrs == 0:
            await ctx.send(
                f"{ctx.author.mention} -> your sleep is 0 hours long - nice try :D"
            )
        elif sleepHrs <= 5:
            if sleepHrs == 1:
                s = ""
            else:
                s = "s"
            await ctx.send(
                f"{ctx.author.mention} -> your sleep is {sleepHrs} hour{s} long - {lessSleepMsg[randint(0, len(lessSleepMsg) - 1)]}"
            )
        else:
            await ctx.send(
                f"{ctx.author.mention} -> your sleep is {sleepHrs} hours long - {moreSleepMsg[randint(0, len(moreSleepMsg) - 1)]}"
            )

    @commands.cooldown(1, 25, type=commands.BucketType.user)
    @commands.command(aliases=["piglin"], usage="[amount of gold]", example="{prefix}barter 64")
    async def barter(self, ctx, gold: int = 64):
        """Barter with Minecraft's Piglin. (Based on JE 1.16.1, before nerf)"""
        # limit gold amount up to 2240 (Minecraft inventory limit)
        if gold > 2240:
            gold = 2240
        if gold <= 0:
            gold = 1

        trade = Piglin(gold)

        items = {}
        for item in trade.items:
            try:
                items[item.name][1] += item.quantity
            except KeyError:
                items[item.name] = [item.id, item.quantity]

        def emoji(name: str):
            return {
                "enchanted-book": "<:enchanted_book:807319425848967258>",
                "iron-boots": "<:enchanted_iron_boots:807319425711210528>",
                "iron-nugget": "<:iron_nuggets:807318404364107776>",
                "splash-potion-fire-res": "<:splashpotionoffireres:807318404024762409>",
                "potion-fire-res": "<:potionoffireres:807318404355719188>",
                "quartz": "<:quartz:807318404285333514>",
                "glowstone-dust": "<:glowstonedust:807318404431085587>",
                "magma-cream": "<:magma_cream:807318404393599046>",
                "ender-pearl": "<:enderpearls:807318454751068180>",
                "string": "<:string:807318404091740216>",
                "fire-charge": "<:fire_charge:807318403894607913>",
                "gravel": "<:garvel:807318404347330610>",
                "leather": "<:leather:807318404385341520>",
                "nether-brick": "<:nether_bricks:807318404020043797>",
                "obsidian": "<:obsidian:807318404318363658>",
                "cry-obsidian": "<:crying_obsidian:807318454423650305>",
                "soul-sand": "<:soul_sand:807318404297785364>",
            }.get(name, "❔")

        e = discord.Embed(
            title="Bartering with {} gold{}  <a:loading:776255339716673566>".format(gold, "s" if gold > 1 else ""),
            colour=discord.Colour.gold()
        )
        e.set_author(
            name=f"{ctx.message.author}",
            icon_url=ctx.message.author.avatar_url,
        )
        a = discord.Embed(
            title="Bartering with {} gold{}".format(gold, "s" if gold > 1 else ""),
            description="You got:\n\n{}".format(
                "\n".join(["{} → {}".format(
                    emoji(v[0]), v[1]) for v in items.values()]
                )
            ),
            colour=discord.Colour.gold(),
        )
        a.set_author(
            name=f"{ctx.message.author}",
            icon_url=ctx.message.author.avatar_url,
        )
        message = await ctx.send(embed=e)
        await asyncio.sleep(5)
        await message.edit(embed=a)

    @commands.cooldown(1, 10, commands.BucketType.guild)
    @commands.command()
    async def joke(self, ctx):
        """`Ask the bot a joke and he will tell you a joke that will defenetly make you laugh no cap`"""
        data = requests.get('https://official-joke-api.appspot.com/jokes/random').json()
        embed = discord.Embed(title = data['setup'], description = data['punchline'], color = 0xf4565a)
        await ctx.send(embed=embed)

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(aliases=['random'])
    async def rng(self, ctx, minimum: int, maximum: int):
        """`Choose a minimum and a maximum number and the bot will choose a random number`"""
        await ctx.send(randint(minimum, maximum))

    @commands.cooldown(1, 10, commands.BucketType.guild)
    @commands.command()
    async def roll(self, ctx, pool):
        """`Roll the dice`"""
        await ctx.send(f"You rolled a {randint(0, int(pool))}")

    @commands.cooldown(1, 10, commands.BucketType.guild)
    @commands.command()
    async def roast (self, ctx, member: discord.Member = None):
        """`Roast Someone >:)`"""
        roast = ["You're as useless as the 'ueue' in 'queue'",
        "If I had a face like yours, I'd sue my parents",
        "Some day you'll go far... and I hope you stay there",
        "You must have been born on a highway cos' that's where most accidents happen",
        "If i had a dollar for every time you said something smart, I'd be broke",
        "When you were born the doctor threw you out the window and the window threw you back",
        "If your brain was dynamite, there wouldn’t be enough to blow your hat off",
        "Your face makes onions cry",
        "I thought of you today, it reminded me to take out the trash",
        "When karma comes back to punch you in the face, I want to be there in case it needs help",
        "I thought I had the flu, but then I realized your face makes me sick to my stomach",
        "You're like Mondays, everyone hates you",
        "Keep rolling your eyes, you might find a barain baxck there",
        "My phone battery lasts longer than your relationships, and my battery only lasts less than an hour FYI",
        "I never forget a face, but in your case I would love to make an exception...",
        "You're so ugly when you look in the mirror your reflection looks away",
        "You're so ugly when you were born, the doctor said aww what a treasure and your mom said yeah lets bury it",
        "Maybe you should eat make-up so you’ll be pretty on the inside too",
        "When you were born, the doctor came out to the waiting room and said to your dad, I'm very sorry. We did everything we could. But he pulled through",
        "It’s a shame you can’t Photoshop your personality.",
        "Whoever told you to be yourself gave you really bad advice",
        "If you could use 100 percent of your brain's power, you'd still be incredibly stupid. 100 percent of nothing is still nothing",
        "Go ahead, tell us everything you know. It'll only take ten seconds",
        "It’s not Halloweeen - take your mask off",
        "You have a face like a smoke alarm. Beat at it until it sounds off",
        "I never saw anybody take so long to type, and with such little result",
        "My hair straightener is hotter than you",
        "I’d explain it to you but I left my English-to-Dumbass Dictionary at home",
        "I don't exactly hate you, but if you were on fire and I had water, I'd drink it",
        "I'd love to insult you, but I'm afraid I cannot perform as well as nature did",
        "Everyone brings happiness to a room. I do when I enter, you do when you leave",
        "The zoo called. They're wondering how you got out of your cage",
        "I suggest you do a little soul searching. You might just find one",
        "I’m visualizing duck tape over your mouth",
        "You should use a glue stick instead of chapstick",
        "I love what you have done to your hair, How'd you get it to come so far of your nostrils?",
        "I would roast you, but my mom said not to burn trash",
        "I'm not saying I hate you, but I would unplug your life support to charge my phone",
        "If tour family were Starwars figures, you'd be the special edition",
        "Over watching paint dry and listening to you, I choose watching paint dry",
        "If you uploaded a video to Youtube with your face, it would get demonetized for `Harmful or dangerous content`",
        "Life is great, you should get one",
        "Fake hair, fake nails, fake smile. Are you sure you weren't made in China?",
        "Your face looks like something I would draw with my non dominant hand.",
        "You're kind of like Rapunzel except instead of letting down your hair, you let down everyone in your life.",
        "I'd agree with you but then we'd both be wrong.",
        "Brains aren't everything, in fact in your case they're nothing.",
        "Why is it acceptable for you to be an idiot but not for me to point it out?",
        "Aww, it’s so cute when you try to talk about things you don’t understand.",
        "At least when I do a handstand my stomach doesn't hit me in the face.",
        "My hair straightener is hotter than you.",
        "If you’re going to be a smart ass, first you have to be smart, otherwise you’re just an ass.",
        "People like you are the reason why people like us need meds and therapy.",
        "Some people drink from the fountain of knowledge - it appears that you merely gargled",
        "When I see your face theres not a thing I would change... Except for the direction im walking in",
        "You sound reasonable... Time to up my medication",
        "I bet your brain feels as good as new, seeing that you never use it",
        "Did your parents ever ask you to run away from home?",
        "Hey, I found your nose, it’s in my business again!",
        "Is your butt jealous of the amount of crap that just came out of your mouth?",
        "Thinking isn't your strong suit, is it?",
        "Roses are red, violets are blue, god made us beautiful, but what happened to you?",
        "Are you in great physical pain, or is that your thinking expression?",
        "Your body fat is about as evenly distributed as wealth in the US economy.",
        "Where’s your off button?",
        "It may be that your whole purpose in life is simply to serve as a warning to others",
        "You're the reason the gene pool needs a lifeguard",
        ]

        no_roast = {
            806990612003946507,
        }

        roast_him_bad = {
            807002219287019561,
        }

        if member is None:
            member = choice(ctx.guild.members)

        if member.id in no_roast:
            a = discord.Embed(
                colour=discord.Color(0xE41919),
                description="Nope, not doing that",
            )

            await ctx.send(embed=a)

        if member.id in roast_him_bad:
            a = discord.Embed(
                colour=discord.Color(0xE41919),
                description="<@807002219287019561> Are you javascript? You're so fucking messy, im a python",
            )

            await ctx.send(embed=a)
        
        else:
            e = discord.Embed(
                colour=discord.Color(0xE41919),
                description=f'{member.mention} {choice(roast)}',
            )

            await ctx.send(embed=e)

    @commands.cooldown(1, 60, commands.BucketType.guild)
    @commands.command()
    async def someone(self, ctx):
        """`Discord's mistake`"""
        await ctx.send(choice(ctx.guild.members).mention)

    @commands.command(aliases=["dl"])
    async def dreamluck(self, ctx):
        """`Test your Minecraft RNG, but in a bot command`"""
        blaze = sum([1 for i in range(306) if random() * 100 <= 50])

        pearl = sum([1 for i in range(263) if random() < (20/473)])

        e = discord.Embed(
            title=f"Your Pearl Trades -> {pearl}/262",
            description="While Dream's luck was -> 42/262",
            colour=discord.Colour(0x08443A),
        )
        a = discord.Embed(
            title=f"Your Blaze Drops -> {blaze}/305",
            description="While Dream's luck was 211/305",
            colour=discord.Colour.gold(),
        )
        await ctx.reply(embed=e)
        await ctx.send(embed=a)

def setup(client):
    client.add_cog(Fun(client))
