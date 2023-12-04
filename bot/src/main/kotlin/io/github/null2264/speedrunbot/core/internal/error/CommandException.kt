package io.github.null2264.speedrunbot.core.internal.error

open class CommandException(message: String = "Something went wrong while executing the command") : Exception(message)