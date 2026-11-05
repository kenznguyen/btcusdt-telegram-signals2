#!/usr/bin/env bash
set -euo pipefail

: "${CM_BUILD_DIR:?Codemagic checkout directory is required}"
: "${CM_ENV:?Codemagic environment file is required}"
android_sdk_root="${ANDROID_SDK_ROOT:-${ANDROID_HOME:-}}"
: "${android_sdk_root:?Android SDK is required on the build machine}"

git -C "$CM_BUILD_DIR" rev-parse HEAD | tee "$CM_BUILD_DIR/android-source-sha.txt"
java -version

tools_dir="$CM_BUILD_DIR/.ci-tools"
cache_dir="$HOME/.cache/five-layer-android"
gradle_zip="$cache_dir/gradle-8.9-bin.zip"
mkdir -p "$tools_dir" "$cache_dir"
if [ ! -f "$gradle_zip" ]; then
  curl --fail --location --retry 3 --connect-timeout 30 \
    https://services.gradle.org/distributions/gradle-8.9-bin.zip \
    --output "$gradle_zip.tmp"
  mv "$gradle_zip.tmp" "$gradle_zip"
fi
# Official binary distribution checksum: https://gradle.org/release-checksums/
printf '%s  %s\n' \
  d725d707bfabd4dfdc958c624003b3c80accc03f7037b5122c4b1d0ef15cecab \
  "$gradle_zip" | shasum -a 256 -c -
unzip -qo "$gradle_zip" -d "$tools_dir"
printf 'GRADLE_BIN=%s\n' "$tools_dir/gradle-8.9/bin/gradle" >> "$CM_ENV"
printf 'ANDROID_SDK_ROOT=%s\n' "$android_sdk_root" >> "$CM_ENV"
"$tools_dir/gradle-8.9/bin/gradle" --version

sdkmanager="$android_sdk_root/cmdline-tools/latest/bin/sdkmanager"
test -x "$sdkmanager"
"$sdkmanager" --sdk_root="$android_sdk_root" \
  --install "platforms;android-35" "build-tools;34.0.0"
printf 'sdk.dir=%s\n' "$android_sdk_root" > "$CM_BUILD_DIR/android-app/local.properties"
