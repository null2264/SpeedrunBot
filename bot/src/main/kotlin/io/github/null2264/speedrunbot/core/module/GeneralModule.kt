package io.github.null2264.speedrunbot.core.module

import dev.kord.core.behavior.edit
import io.github.null2264.speedrunbot.core.Bot
import io.github.null2264.speedrunbot.core.internal.annotation.Command
import io.github.null2264.speedrunbot.core.internal.Context
import io.github.null2264.speedrunbot.core.internal.BotModule
import kotlinx.datetime.Clock

class GeneralModule(override val bot: Bot) : BotModule(bot, "General", "idk") {
    @Command(description = "Ping the bot!")
    private suspend fun ping(ctx: Context) {
        val startTime = Clock.System.now()
        ctx.typing()
        val endTime = Clock.System.now()
        ctx.send("Pong! ${endTime.toEpochMilliseconds() - startTime.toEpochMilliseconds()}ms")
    }

    @Command("yep")
    private suspend fun lmao(ctx: Context) {
        ctx.send("Hello World!")
    }
}