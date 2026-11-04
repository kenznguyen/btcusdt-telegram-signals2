import org.gradle.api.tasks.testing.Test

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
}

android {
    namespace = "com.kenznguyen.btclivealerts"
    compileSdk = 35
    ndkVersion = "27.2.12479018"

    externalNativeBuild {
        cmake {
            path = file("src/main/cpp/CMakeLists.txt")
            version = "3.22.1"
        }
    }

    defaultConfig {
        applicationId = "com.kenznguyen.btclivealerts"
        minSdk = 26
        targetSdk = 35
        versionCode = 2
        versionName = "0.2.0"
        buildConfigField("boolean", "PARALLEL_INSTALL", "false")
        ndk {
            abiFilters += listOf("arm64-v8a", "armeabi-v7a", "x86", "x86_64")
        }
        externalNativeBuild {
            cmake {
                arguments += listOf(
                    "-DSQLITE_AMALGAMATION_DIR=${project.layout.buildDirectory.dir("generated/sqlite/vendor").get().asFile.absolutePath}",
                    "-DSQLITE_PIN_FILE=${project.layout.buildDirectory.file("generated/sqlite/sqlite3-pins.cmake").get().asFile.absolutePath}"
                )
            }
        }
    }

    signingConfigs {
        create("release") {
            storeFile = file(System.getenv("ANDROID_KEYSTORE_PATH") ?: "missing-release.keystore")
            storePassword = System.getenv("ANDROID_KEYSTORE_PASSWORD")
            keyAlias = System.getenv("ANDROID_KEY_ALIAS")
            keyPassword = System.getenv("ANDROID_KEY_PASSWORD")
        }
    }

    buildTypes {
        create("parallel") {
            initWith(getByName("debug"))
            applicationIdSuffix = ".paper"
            versionNameSuffix = "-paper"
            matchingFallbacks += listOf("debug")
            signingConfig = signingConfigs.getByName("release")
            buildConfigField("boolean", "PARALLEL_INSTALL", "true")
        }
        getByName("release") {
            isMinifyEnabled = false
            signingConfig = signingConfigs.getByName("release")
        }
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }
}

dependencies {
    implementation(platform("androidx.compose:compose-bom:2024.12.01"))
    implementation("androidx.activity:activity-compose:1.10.0")
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-graphics")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.8.7")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.9.0")
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    debugImplementation("androidx.compose.ui:ui-tooling")
    testImplementation("junit:junit:4.13.2")
    testImplementation("org.json:json:20240303")
    testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.9.0")
}




// CI may supply a D5 wire fixture emitted by the isolated native :memory: harness.
tasks.withType<Test>().configureEach {
    val fixture = providers.gradleProperty("d5NativeFixture").orNull
    systemProperty("d5.native.fixture.path", fixture.orEmpty())
    systemProperty("d5.native.fixture.required", (fixture != null).toString())
}
