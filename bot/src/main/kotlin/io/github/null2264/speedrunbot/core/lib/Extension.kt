package io.github.null2264.speedrunbot.core.lib

import dev.kord.core.entity.User

object Extension {
    fun String.hasPrefix(vararg prefixes: String): Pair<String, String>? {
        if (this.isBlank()) return null

        var ret: Pair<String, String>? = null

        prefixes.forEach {
            if (this.substring(0, it.length) == it) {
                ret = Pair(this.substring(0, it.length), this.substring(it.length))
                return@forEach
            }
        }

        return ret
    }

    val User.string
        get() = "$username#$discriminator"
}