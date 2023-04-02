package io.github.null2264.speedrunbot.core.internal

import kotlin.reflect.KFunction

data class CommandObj(
    val name: String,
    val extension: String,
    val callback: KFunction<*>,
    val description: String? = null,
)