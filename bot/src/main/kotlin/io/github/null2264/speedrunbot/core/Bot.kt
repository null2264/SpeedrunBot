package io.github.null2264.speedrunbot.core

import dev.kord.core.Kord
import dev.kord.core.entity.Message
import dev.kord.core.event.gateway.ReadyEvent
import dev.kord.core.event.message.MessageCreateEvent
import dev.kord.core.on
import dev.kord.gateway.Intent
import dev.kord.gateway.PrivilegedIntent
import io.github.null2264.speedrunbot.core.internal.BotModule
import io.github.null2264.speedrunbot.core.internal.Command
import io.github.null2264.speedrunbot.core.internal.Context
import io.github.null2264.speedrunbot.core.internal.error.CommandException
import io.github.null2264.speedrunbot.core.internal.error.CommandNotFound
import io.github.null2264.speedrunbot.core.lib.Extension.hasPrefix
import io.github.null2264.speedrunbot.core.lib.Extension.string
import kotlin.reflect.KClass
import kotlin.reflect.KFunction
import kotlin.reflect.full.callSuspend
import kotlin.reflect.full.isSubclassOf

class Bot(block: (Bot.() -> Unit)? = null) {
    private var _kord: Kord? = null
    private suspend fun kord(): Kord {
        if (this._kord == null)
            _kord = Kord(System.getenv("TOKEN")).apply {
                on<ReadyEvent> {
                    println("Online! ${self.string}")
                }

                on<MessageCreateEvent> { onMessage(this.message, this) }
            }
        return _kord!!
    }

    // Data
    private val _commands = mutableMapOf<String, Command>()
    val commands: Map<String, Command> get() = _commands
    private val _extensions = mutableMapOf<String, BotModule>()
    val extensions: Map<String, BotModule> get() = _extensions
    private var prefixes: List<String> = listOf()

    // Setter/Getter
    fun commands(command: Command, name: String? = null) {
        _commands[if (name.isNullOrEmpty()) command.name else name] = command
    }

    fun extensions(vararg extensions: KFunction<BotModule>) {
        extensions(extensions.toList())
    }

    fun extensions(extensions: List<KFunction<BotModule>>) {
        for (ext in extensions) {
            val kClass = ext.returnType.classifier as KClass<*>
            if (!kClass.isSubclassOf(BotModule::class))
                continue

            ext.call(this).also{ module ->
                module.setup()
                this@Bot._extensions[module.name] = module
            }
        }
    }

    fun prefixes(vararg prefixes: String) {
        prefixes(prefixes.toList())
    }

    fun prefixes(prefixes: List<String>) {
        this.prefixes = prefixes
    }

    init {
        if (block != null)
            block()
    }

    suspend fun start() {
        kord().login {
            @OptIn(PrivilegedIntent::class)
            intents += Intent.MessageContent
        }
    }

    suspend fun stop() {
        kord().shutdown()
    }

    private fun getContext(message: Message): Context {
        val candidate = message.content.hasPrefix(*prefixes.toTypedArray())
        return Context(this, message, candidate?.first, candidate?.second)
    }

    suspend fun onCommandError(context: Context, error: CommandException) {
        context.send(error.message!!)
    }

    suspend fun processCommand(message: Message) {
        val ctx = getContext(message)

        try {
            ctx.command?.let { command ->
                command.callback.callSuspend(extensions[command.extension], this)
            } ?: throw CommandNotFound()
        } catch (e: CommandException) {
            onCommandError(ctx, e)
        }
    }

    suspend fun onMessage(message: Message, event: MessageCreateEvent) {
        if (message.author?.isBot != false) return

        processCommand(message)
    }
}