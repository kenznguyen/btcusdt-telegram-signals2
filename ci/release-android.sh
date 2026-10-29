#!/usr/bin/env bash
set -euo pipefail

: "${CM_BUILD_DIR:?Codemagic checkout directory is required}"
: "${CHART_GRADLE_BIN:?Run ci/setup-android.sh first}"
: "${ANDROID_SDK_ROOT:?Android SDK is required}"
: "${ANDROID_KEYSTORE_BASE64:?Configure the existing release keystore in android_release}"
: "${ANDROID_KEYSTORE_PASSWORD:?Configure the release keystore password}"
: "${ANDROID_KEY_ALIAS:?Configure the existing release key alias}"
: "${ANDROID_KEY_PASSWORD:?Configure the release key password}"
test "$ANDROID_KEY_ALIAS" = 'btc-chart-release'

chart_key_dir="$(mktemp -d)"
export ANDROID_KEYSTORE_PATH="$chart_key_dir/release.keystore"
trap 'rm -f "$ANDROID_KEYSTORE_PATH"; rmdir "$chart_key_dir"' EXIT
python3 - <<'PY'
import base64
import os
from pathlib import Path

encoded = ''.join(os.environ['ANDROID_KEYSTORE_BASE64'].split())
decoded = base64.b64decode(encoded, validate=True)
if not decoded:
    raise ValueError('Release keystore is empty')
path = Path(os.environ['ANDROID_KEYSTORE_PATH'])
path.write_bytes(decoded)
path.chmod(0o600)
PY

cd "$CM_BUILD_DIR/android-app"
"$CHART_GRADLE_BIN" :app:testDebugUnitTest --no-daemon --stacktrace
"$CHART_GRADLE_BIN" :app:assembleRelease --no-daemon --stacktrace

"$ANDROID_SDK_ROOT/build-tools/34.0.0/apksigner" verify --verbose --print-certs \
  "$CM_BUILD_DIR/android-app/app/build/outputs/apk/release/app-release.apk" \
  | tee "$CM_BUILD_DIR/android-release-apk-signature.txt"

# Verify that the built APK actually uses the supplied keystore certificate.
# The public fingerprint is an artifact; the keystore and passwords are not.
python3 - <<'PY'
import hashlib
import os
import re
import subprocess
from pathlib import Path

certificate = subprocess.check_output([
    'keytool', '-exportcert', '-keystore', os.environ['ANDROID_KEYSTORE_PATH'],
    '-alias', os.environ['ANDROID_KEY_ALIAS'], '-storepass:env', 'ANDROID_KEYSTORE_PASSWORD',
])
expected = hashlib.sha256(certificate).hexdigest()
signature = Path(os.environ['CM_BUILD_DIR'], 'android-release-apk-signature.txt').read_text()
signers = re.findall(r'^Signer #\d+ certificate SHA-256 digest: ([0-9a-fA-F]+)$', signature, re.MULTILINE)
if not signers or set(value.lower() for value in signers) != {expected}:
    raise ValueError('APK signing certificate does not match the supplied release keystore')
print('Verified release certificate SHA-256:', expected)
PY
