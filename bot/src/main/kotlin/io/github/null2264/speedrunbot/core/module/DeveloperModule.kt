package io.github.null2264.speedrunbot.core.module

import dev.kord.core.behavior.edit
import io.github.null2264.speedrunbot.core.Bot
import io.github.null2264.speedrunbot.core.internal.annotation.Command
import io.github.null2264.speedrunbot.core.internal.Context
import io.github.null2264.speedrunbot.core.internal.BaseModule
import io.github.null2264.speedrunbot.core.internal.CommandObj
import kotlinx.datetime.Clock
import kotlin.reflect.jvm.isAccessible
import kotlin.reflect.jvm.kotlinFunction

class DeveloperModule(override val bot: Bot) : BaseModule(bot, "Developer", "Only for developers") {
    @Command("poweroff")
    private suspend fun shutdown(ctx: Context) {
        ctx.reply("Shutting Down...", mentionsAuthor = true)
        bot.stop()
    }
}