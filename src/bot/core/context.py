from typing import TYPE_CHECKING

from discord.ext.commands import Context


if TYPE_CHECKING:
    from .bot import MangoManBot


class MMContext(Context):
    if TYPE_CHECKING:
        bot: MangoManBot
