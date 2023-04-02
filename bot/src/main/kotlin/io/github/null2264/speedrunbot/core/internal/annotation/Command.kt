package io.github.null2264.speedrunbot.core.internal.annotation


/**
 * Annotation to tag a function as command
 *
 * @param name the command's name
 * @param description the command's description
 * @param help the command's extended description (a more detailed description)
 */
@Retention(AnnotationRetention.RUNTIME)
@Target(AnnotationTarget.FUNCTION)
annotation class Command(val name: String = "", val description: String = "", val help: String = "")