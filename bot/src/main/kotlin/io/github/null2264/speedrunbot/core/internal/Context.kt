package io.github.null2264.speedrunbot.core.internal

import dev.kord.core.behavior.channel.createMessage
import dev.kord.core.entity.Message
import dev.kord.rest.builder.message.AllowedMentionsBuilder
import dev.kord.rest.builder.message.create.allowedMentions
import io.github.null2264.speedrunbot.core.Bot

class Context(private val bot: Bot, private val message: Message, val prefix: String?, private val _command: String?) {
    val author get() = message.author
    val command get() = bot.commands[_command]

    suspend fun send(content: String) = message.channel.createMessage(content)

    suspend fun reply(content: String, mentionsAuthor: Boolean = false) = message.channel.createMessage {
        this.content = content
        messageReference = message.id
        if (!mentionsAuthor)
            allowedMentions {
                AllowedMentionsBuilder().repliedUser
            }
    }
}