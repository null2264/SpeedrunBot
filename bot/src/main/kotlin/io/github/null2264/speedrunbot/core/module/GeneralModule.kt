package io.github.null2264.speedrunbot.core.module

import dev.kord.core.behavior.edit
import io.github.null2264.speedrunbot.core.Bot
import io.github.null2264.speedrunbot.core.internal.annotation.Command
import io.github.null2264.speedrunbot.core.internal.Context
import io.github.null2264.speedrunbot.core.internal.BaseModule
import kotlinx.datetime.Clock

class GeneralModule(override val bot: Bot) : BaseModule(bot, "General", "idk") {
    @Command
    private suspend fun ping(ctx: Context) {
        val startTime = Clock.System.now()
        val msg = ctx.send("Pong!")
        val endTime = Clock.System.now()
        msg.edit {
            content = "Pong! ${endTime.toEpochMilliseconds() - startTime.toEpochMilliseconds()}ms"
        }
    }

    @Command("yep")
    private suspend fun lmao(ctx: Context) {
        ctx.send("Hello World!")
    }
}