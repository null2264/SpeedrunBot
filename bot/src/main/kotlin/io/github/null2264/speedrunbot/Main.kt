package io.github.null2264.speedrunbot

import io.github.null2264.speedrunbot.core.Bot
import io.github.null2264.speedrunbot.core.di.appModule
import io.github.null2264.speedrunbot.core.module.DeveloperModule
import io.github.null2264.speedrunbot.core.module.GeneralModule
import org.koin.core.context.GlobalContext.startKoin

suspend fun main() {
    startKoin {
        modules(appModule)
    }

    Bot {
        prefixes("src!", "mm!") // mm! for backwards compatibility

        extensions(::DeveloperModule, ::GeneralModule)
    }.start()
}