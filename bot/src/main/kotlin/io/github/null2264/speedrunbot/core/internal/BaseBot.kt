package io.github.null2264.speedrunbot.core.internal

import dev.kord.core.Kord
import dev.kord.core.entity.Message
import dev.kord.core.event.gateway.ReadyEvent
import dev.kord.core.event.message.MessageCreateEvent
import dev.kord.core.on
import dev.kord.gateway.Intent
import dev.kord.gateway.PrivilegedIntent
import io.github.null2264.speedrunbot.core.lib.Extension.hasPrefix
import io.github.null2264.speedrunbot.core.lib.Extension.string
import io.ktor.util.reflect.*
import kotlin.reflect.KClass
import kotlin.reflect.KFunction
import kotlin.reflect.full.callSuspend
import kotlin.reflect.full.isSubclassOf

abstract class BaseBot(block: (BaseBot.() -> Unit)? = null) {
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
    internal val _commands = mutableMapOf<String, CommandObj>()
    val commands: Map<String, CommandObj> get() = _commands
    internal val _extensions = mutableMapOf<String, BaseModule>()
    val extensions: Map<String, BaseModule> get() = _extensions
    private var prefixes: List<String> = listOf()

    // Setter/Getter
    fun commands(command: CommandObj, name: String? = null) {
        _commands[if (name.isNullOrEmpty()) command.name else name] = command
    }

    fun extensions(vararg extensions: KFunction<BaseModule>) {
        extensions(extensions.toList())
    }

    fun extensions(extensions: List<KFunction<BaseModule>>) {
        for (ext in extensions) {
            val kClass = ext.returnType.classifier as KClass<*>
            if (!kClass.isSubclassOf(BaseModule::class))
                continue

            ext.call(this).also{ module ->
                module.setup()
                this@BaseBot._extensions[module.name] = module
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

    open suspend fun start() {
        kord().login {
            @OptIn(PrivilegedIntent::class)
            intents += Intent.MessageContent
        }
    }

    open suspend fun stop() {
        kord().shutdown()
    }

    open suspend fun onMessage(message: Message, event: MessageCreateEvent) {
        if (message.author?.isBot != false) return

        val result = message.content.hasPrefix(*prefixes.toTypedArray())

        if (result != null) {
            val context = Context(message, result)
            context.apply {
                try {
                    val actualCommand = commands[command]
                    if (actualCommand == null) {
                        println("Not found")
                        return
                    }
                    actualCommand.callback.callSuspend(extensions[actualCommand.extension], this)
                } catch (e: Exception) {
                    println(e)
                }
            }
        }
    }
}