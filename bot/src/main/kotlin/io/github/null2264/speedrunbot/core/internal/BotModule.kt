package io.github.null2264.speedrunbot.core.internal

import io.github.null2264.speedrunbot.core.internal.annotation.Command as COMMAND
import kotlin.reflect.jvm.isAccessible
import kotlin.reflect.jvm.kotlinFunction

abstract class BotModule(open val bot: BaseBot, val name: String, val description: String? = null) {
    fun setup() {
        val methods = this::class.java.declaredMethods
        for (method in methods) {
            for (annotation in method.annotations) {
                if (annotation !is COMMAND)
                    continue

                bot.apply {
                    val kMethod = method.kotlinFunction
                    if (bot.commands[kMethod?.name] != null) {
                        println("Command already exists")
                        return
                    }
                    kMethod?.let {
                        it.isAccessible = true
                        commands(
                            Command(
                                annotation.name.ifEmpty { it.name },
                                this@BotModule.name,
                                it,
                                annotation.description.ifEmpty { description },
                            )
                        )
                    }
                }
            }
        }
    }
}