package io.github.null2264.speedrunbot.core.internal

import io.github.null2264.speedrunbot.core.internal.annotation.Command
import kotlin.reflect.jvm.isAccessible
import kotlin.reflect.jvm.kotlinFunction

abstract class BaseModule(open val bot: BaseBot, val name: String, val description: String? = null) {
    fun setup() {
        val methods = this::class.java.declaredMethods
        for (method in methods) {
            for (annotation in method.annotations) {
                if (annotation !is Command)
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
                            CommandObj(
                                annotation.name.ifEmpty { it.name },
                                this@BaseModule.name,
                                it,
                            )
                        )
                    }
                }
            }
        }
    }
}