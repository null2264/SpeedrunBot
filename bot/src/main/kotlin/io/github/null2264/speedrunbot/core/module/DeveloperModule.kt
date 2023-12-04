package io.github.null2264.speedrunbot.core.module

import io.github.null2264.speedrunbot.core.Bot
import io.github.null2264.speedrunbot.core.internal.annotation.Command
import io.github.null2264.speedrunbot.core.internal.Context
import io.github.null2264.speedrunbot.core.internal.BotModule

class DeveloperModule(override val bot: Bot) : BotModule(bot, "Developer", "Only for developers") {
    @Command(
        name="poweroff",
        description="Turn the bot off",
    )
    private suspend fun shutdown(ctx: Context) {
        ctx.reply("Shutting Down...", mentionsAuthor = true)
        bot.stop()
    }
}