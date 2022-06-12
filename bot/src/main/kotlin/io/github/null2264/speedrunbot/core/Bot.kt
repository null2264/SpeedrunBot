package io.github.null2264.speedrunbot.core

import dev.kord.core.Kord
import dev.kord.core.behavior.edit
import dev.kord.core.entity.Message
import dev.kord.core.event.gateway.ReadyEvent
import dev.kord.core.event.message.MessageCreateEvent
import dev.kord.core.on
import dev.kord.gateway.Intent
import dev.kord.gateway.PrivilegedIntent
import io.github.null2264.speedrunbot.core.lib.Extension.hasPrefix
import io.github.null2264.speedrunbot.core.lib.Extension.string
import kotlinx.datetime.Clock

class Bot {
    private var _kord: Kord? = null
    private val kord get() = _kord!!

    suspend fun start() {
        _kord = Kord(System.getenv("TOKEN")).apply {
            on<ReadyEvent> {
                println("Online! ${self.string}")
            }

            on<MessageCreateEvent> {
                onMessage(this.message, this)
            }
        }

        kord.login {
            @OptIn(PrivilegedIntent::class)
            intents += Intent.MessageContent
        }
    }

    private suspend fun onMessage(message: Message, event: MessageCreateEvent) {
        if (message.author?.isBot != false) return
        val result = message.content.hasPrefix("!", ">", "zi>")

        if (result != null) {
            val context = Context(message, result)
            context.apply {
                when (command) {
                    "ping" -> {
                        val startTime = Clock.System.now()
                        val msg = send("Pong!")
                        val endTime = Clock.System.now()
                        msg.edit {
                            content = "Pong! ${endTime.toEpochMilliseconds() - startTime.toEpochMilliseconds()}ms"
                        }
                    }
                    "test" -> reply("Hello World!")
                    "poweroff" -> {
                        reply("Shutting Down...", mentionsAuthor = true)
                        kord.shutdown()
                    }
                    "about" -> send("Discord Bot using Kotlin!")
                    else -> {}
                }
            }
        }
    }
}