plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
}

android {
    namespace = "com.kenznguyen.btclivealerts"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.kenznguyen.btclivealerts"
        minSdk = 26
        targetSdk = 35
        versionCode = 3
        versionName = "0.3.0"
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
        getByName("release") {
            isMinifyEnabled = false
            signingConfig = signingConfigs.getByName("release")
        }
    }

    buildFeatures { compose = true }
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
}

tasks.withType<Test>().configureEach {
    val parityTrace = System.getenv("ANDROID_PARITY_TRACE_OUTPUT")
    if (!parityTrace.isNullOrBlank()) {
        systemProperty("android.parity.trace.output", parityTrace)
    }
}

tasks.withType<Test>().configureEach {
    System.getenv("ANDROID_PARITY_ENTRY_TRACE_OUTPUT")?.takeIf { it.isNotBlank() }?.let {
        systemProperty("android.parity.entry.trace.output", it)
    }
}

tasks.withType<Test>().configureEach {
    System.getenv("ANDROID_PARITY_DCA_TRACE_OUTPUT")?.takeIf { it.isNotBlank() }?.let {
        systemProperty("android.parity.dca.trace.output", it)
    }
}

tasks.withType<Test>().configureEach {
    System.getenv("ANDROID_PARITY_TP_TRACE_OUTPUT")?.takeIf { it.isNotBlank() }?.let {
        systemProperty("android.parity.tp.trace.output", it)
    }
}

// Opt-in offline Kotlin replay: same OKX Futures CSVs as Freqtrade, never network calls.
tasks.withType<Test>().configureEach {
    System.getenv("OKX_PARITY_OHLCV_DIR")?.takeIf { it.isNotBlank() }?.let {
        systemProperty("okx.parity.ohlcv.dir", it)
    }
    System.getenv("OKX_PARITY_ANDROID_EVENTS")?.takeIf { it.isNotBlank() }?.let {
        systemProperty("okx.parity.android.events", it)
    }
}
