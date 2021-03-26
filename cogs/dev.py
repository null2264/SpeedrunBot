import asyncio
import discord
import os
import re
import sys

from asyncio.subprocess import PIPE, STDOUT
from discord.ext import commands, menus
from cogs.utilities.paginator import MMMenu


SHELL = os.getenv("SHELL") or "/bin/bash"
WINDOWS = sys.platform == "win32"


class ShellResult:
    def __init__(self, status, stdout, stderr):
        self.status = status
        self._stdout = stdout or ""
        self._stderr = stderr or ""
        if stdout is not None:
            self.stdout = stdout.decode("utf-8")
        else:
            self.stdout = None
        if stderr is not None:
            self.stderr = stderr.decode("utf-8")
        else:
            self.stderr = None

    def __repr__(self):
        return f"<Result status={self.status} stdout={len(self._stdout)} stderr={len(self._stderr)}>"


class TextWrapPageSource(menus.ListPageSource):
    def __init__(self, prefix, lang, raw_text, max_size: int = 1024):
        size_limit = len(prefix) * 2 + len(lang) + max_size
        text = [raw_text]
        n = 0
        while len(text[n]) > size_limit:
            text.append(text[n][size_limit:])
            text[n] = text[n][:size_limit]
            n += 1
        super().__init__(entries=text, per_page=1)
        self.lang = lang
        self.prefix = prefix + lang + "\n"
        self.suffix = prefix

    async def format_page(self, menu, text):
        e = discord.Embed(
            title="Shell",
            description=self.prefix + text + self.suffix,
            colour=discord.Colour(0xFFFFF0),
        )
        return e


class CodeBlock(object):
    __slots__ = ("language", "code")

    def __init__(self, language, code):
        self.language = "".join(language) or "sh"
        self.code = "".join(code) or "echo ''"


class codeBlockConverter(commands.Converter):
    """Get command out of codeblock."""

    async def convert(self, ctx, argument: str):
        if not argument.startswith("`"):
            return CodeBlock("sh", argument)

        backticks = 0
        inLanguage = False
        inCode = False
        language = []
        code = []

        for char in argument:
            if not inCode and not inLanguage:
                if char == "`":
                    backticks += 1
                    if backticks > 3 and not code:
                        break
                elif backticks == 3:
                    inLanguage = True
            if inLanguage and char != "\n":
                language.append(char)

            if char == "\n":
                inLanguage = False
                inCode = True
            if char != "`" and (inCode or backticks == 1):
                inCode = True
                if not code and char in (" ", "\n"):
                    # "char" instead of " char" or "\nchar"
                    pass
                else:
                    code.append(char)
            elif code == "`" and inCode:
                break

        return CodeBlock(language, code)


class Developer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        """Only bot masters able to use debug/developer cog."""
        return ctx.author.id in self.bot.master

    @commands.command(aliases=["sh"], usage="(shell command)")
    async def shell(self, ctx, *, command: codeBlockConverter):
        """Execute shell command from discord. **Use with caution**"""
        if command.code.startswith("sudo") or command.code.startswith("yes"):
            return await ctx.reply("Command {} is not allowed!".format(command.code))

        if WINDOWS:
            return await ctx.reply("Unfortunately, Windows is not supported.")
        else:
            sequence = (SHELL, "-c", str(command.code))

        async def run(shell_command):
            p = await asyncio.create_subprocess_exec(
                *shell_command, stdout=PIPE, stderr=STDOUT
            )
            stdout, stderr = await p.communicate()
            code = p.returncode
            return ShellResult(code, stdout, stderr)

        # TODO: Make shell command not stuck
        # try:
        #     proc = await asyncio.wait_for(run(sequence), timeout=5)
        # except asyncio.TimeoutError:
        #     proc = None
        proc = await run(sequence)

        def clean_bytes(line):
            """
            Cleans a byte sequence of shell directives and decodes it.
            """
            text = line.replace("\r", "").strip("\n")
            return re.sub(r"\x1b[^m]*m", "", text).replace("``", "`\u200b`").strip("\n")

        content = clean_bytes(proc.stdout if proc else "{}: timeout!".format(SHELL))
        menus = MMMenu(TextWrapPageSource("```", command.language, content))
        return await menus.start(ctx)

    @commands.command()
    async def pull(self, ctx):
        """Update the bot from github."""
        await ctx.invoke(
            self.bot.get_command("sh"), command=CodeBlock("sh", "git pull")
        )


def setup(bot):
    bot.add_cog(Developer(bot))
