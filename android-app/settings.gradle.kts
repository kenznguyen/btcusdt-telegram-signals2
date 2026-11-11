pluginManagement {
    repositories {
        maven {
            name = "GoogleCloudMavenCentralMirror"
            url = uri("https://maven-central.storage-download.googleapis.com/maven2/")
        }
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        maven {
            name = "GoogleCloudMavenCentralMirror"
            url = uri("https://maven-central.storage-download.googleapis.com/maven2/")
        }
        google()
        mavenCentral()
    }
}
rootProject.name = "BTCUSDTQuantSystem"
include(":app")
