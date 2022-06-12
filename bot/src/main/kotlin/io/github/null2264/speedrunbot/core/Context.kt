package io.github.null2264.speedrunbot.core

import dev.kord.core.behavior.channel.createMessage
import dev.kord.core.entity.Message
import dev.kord.rest.builder.message.AllowedMentionsBuilder
import dev.kord.rest.builder.message.create.allowedMentions

class Context(private val message: Message, private val pair: Pair<String, String>) {
    val author get() = message.author
    val prefix get() = pair.first
    val command get() = pair.second

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