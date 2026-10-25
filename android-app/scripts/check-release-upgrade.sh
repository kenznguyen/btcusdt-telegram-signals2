#!/usr/bin/env bash
# Usage: check-release-upgrade.sh installed-release.apk candidate-release.apk
# Never reads or exposes private signing keys.
set -euo pipefail
if [[ $# -ne 2 ]]; then
  echo "Usage: $0 installed-release.apk candidate-release.apk" >&2
  exit 2
fi
old="$1"; new="$2"
[[ -s "$old" && -s "$new" ]] || { echo "Both APK files must exist" >&2; exit 2; }
sdk="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-}}"
[[ -n "$sdk" && -d "$sdk/build-tools" ]] || { echo "ANDROID_HOME/build-tools required" >&2; exit 2; }
aapt="$(find "$sdk/build-tools" -type f -name aapt | sort -V | tail -n 1)"
signer="$(find "$sdk/build-tools" -type f -name apksigner | sort -V | tail -n 1)"
[[ -x "$aapt" && -x "$signer" ]] || { echo "Missing aapt or apksigner" >&2; exit 2; }
metadata() { "$aapt" dump badging "$1" | grep -m 1 '^package:'; }
package() { sed -n "s/.*name='\\([^']*\\)'.*/\\1/p" <<< "$1"; }
version() { sed -n "s/.*versionCode='\\([0-9]*\\)'.*/\\1/p" <<< "$1"; }
fingerprint() {
  "$signer" verify --print-certs "$1" |
    sed -nE 's/.*[Cc]ertificate SHA-256 digest: ([[:xdigit:]]+).*/\\1/p' |
    tr '[:upper:]' '[:lower:]' | sort -u
}
old_meta="$(metadata "$old")"
new_meta="$(metadata "$new")"
old_package="$(package "$old_meta")"; new_package="$(package "$new_meta")"
old_version="$(version "$old_meta")"; new_version="$(version "$new_meta")"
[[ -n "$old_package" && -n "$new_package" && -n "$old_version" && -n "$new_version" ]] ||
  { echo "Cannot read APK metadata" >&2; exit 1; }
old_cert="$(fingerprint "$old")"; new_cert="$(fingerprint "$new")"
[[ -n "$old_cert" && -n "$new_cert" ]] || { echo "Missing signing certificate" >&2; exit 1; }
echo "Installed: $old_package versionCode=$old_version certificate=$old_cert"
echo "Candidate: $new_package versionCode=$new_version certificate=$new_cert"
[[ "$old_package" == "$new_package" ]] || { echo "FAIL: package ID differs" >&2; exit 1; }
[[ "$old_cert" == "$new_cert" ]] || { echo "FAIL: signing certificates differ" >&2; exit 1; }
(( 10#$new_version > 10#$old_version )) || { echo "FAIL: versionCode must increase" >&2; exit 1; }
echo "PASS: APK package, signer and versionCode support direct upgrade."
