package io.github.null2264.speedrunbot.core.internal

import kotlin.reflect.KFunction

/**
 * Class holding information about a command
 */
data class Command(
    val name: String,
    val extension: String,
    val callback: KFunction<*>,
    val description: String? = null,
)