import org.jetbrains.kotlin.gradle.tasks.KotlinCompile

plugins {
    kotlin("jvm") version "1.7.0"
    application
}

group = "com.github.null2264"
version = "0.1"

dependencies {
    implementation("dev.kord:kord-core:0.8.x-SNAPSHOT")
    implementation("io.insert-koin:koin-core:3.2.0")
    implementation(kotlin("reflect"))
}

application {
    mainClass.set("io.github.null2264.speedrunbot.MainKt")
}