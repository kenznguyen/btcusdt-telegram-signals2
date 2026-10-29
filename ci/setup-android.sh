#!/usr/bin/env bash
set -euo pipefail

: "${CM_BUILD_DIR:?Codemagic checkout directory is required}"
: "${CM_ENV:?Codemagic environment file is required}"
chart_sdk_root="${ANDROID_SDK_ROOT:-${ANDROID_HOME:-}}"
: "${chart_sdk_root:?Android SDK is required on the build machine}"

git -C "$CM_BUILD_DIR" rev-parse HEAD | tee "$CM_BUILD_DIR/android-source-sha.txt"
java -version

chart_tools_dir="$CM_BUILD_DIR/.ci-tools"
chart_cache_dir="$HOME/.cache/btc-chart-pro"
chart_gradle_zip="$chart_cache_dir/gradle-8.9-bin.zip"
mkdir -p "$chart_tools_dir" "$chart_cache_dir"
if [ ! -f "$chart_gradle_zip" ]; then
  curl --fail --location --retry 3 --connect-timeout 30 \
    https://services.gradle.org/distributions/gradle-8.9-bin.zip \
    --output "$chart_gradle_zip.tmp"
  mv "$chart_gradle_zip.tmp" "$chart_gradle_zip"
fi
# Official binary distribution checksum: https://gradle.org/release-checksums/
printf '%s  %s\n' \
  d725d707bfabd4dfdc958c624003b3c80accc03f7037b5122c4b1d0ef15cecab \
  "$chart_gradle_zip" | shasum -a 256 -c -
unzip -qo "$chart_gradle_zip" -d "$chart_tools_dir"
printf 'CHART_GRADLE_BIN=%s\n' "$chart_tools_dir/gradle-8.9/bin/gradle" >> "$CM_ENV"
printf 'ANDROID_SDK_ROOT=%s\n' "$chart_sdk_root" >> "$CM_ENV"
"$chart_tools_dir/gradle-8.9/bin/gradle" --version

# AGP 8.7.3 uses Build Tools 34.0.0 even with compileSdk 35.
chart_sdkmanager="$chart_sdk_root/cmdline-tools/latest/bin/sdkmanager"
test -x "$chart_sdkmanager"
"$chart_sdkmanager" --sdk_root="$chart_sdk_root" \
  --install "platforms;android-35" "build-tools;34.0.0"
printf 'sdk.dir=%s\n' "$chart_sdk_root" > "$CM_BUILD_DIR/android-app/local.properties"
