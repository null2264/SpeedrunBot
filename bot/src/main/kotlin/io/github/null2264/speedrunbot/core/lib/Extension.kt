package io.github.null2264.speedrunbot.core.lib

import dev.kord.core.entity.User

object Extension {
    /**
     * Ternary-like if statement
     *
     * Example:
     * - `J/JS/C` = `statement ? true : false`
     * - `K`      = `(statement) then true ?: false`
     * - `K + λ`  = `(statement) then { some actions } ?: false`
     * - `OG K`   = `if (statement) true else false`
     */
    inline infix fun <T> Boolean.then(ifTrue: () -> T): T? = if (this) ifTrue() else null
    inline infix fun <T> Boolean.then(ifTrue: T): T? = (this) then { ifTrue }

    fun String.hasPrefix(vararg prefixes: String): Pair<String, String>? {
        if (this.isBlank()) return null

        var ret: Pair<String, String>? = null

        prefixes.forEach {
            (this.substring(0, it.length) == it) then {
                ret = Pair(this.substring(0, it.length), this.substring(it.length))
                return@forEach
            }
        }

        return ret
    }

    val User.string
        get() = "$username#$discriminator"

}