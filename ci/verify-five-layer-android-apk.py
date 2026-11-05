#!/usr/bin/env python3
"""Verify the single five-layer Paper APK and reject Chart Pro payloads."""

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import zipfile


EXPECTED_PACKAGE = "com.kenznguyen.fivelayerpaper"
EXPECTED_LABEL = "BTCUSDT Quant System · 5 Tầng"
EXPECTED_ACTIVITY = "com.kenznguyen.btclivealerts.MainActivity"
FORBIDDEN_DEX_MARKERS = (
    b"CompleteDashboard",
    b"StrategyMonitorService",
    b"MultiSymbolScanner",
    b"ScannerMarketFeed",
    b"BacktestPanel",
    b"AlertDelivery",
    b"MarketEngine",
    b"OrderBookEngine",
    b"OrderBookPanel",
    b"OrderBookSequence",
    b"ChartAnalytics",
    b"ChartMarketSession",
    b"StrategyEngine",
)


def badging(output):
    packages = re.findall(
        r"^package: name='([^']+)' versionCode='([0-9]+)' versionName='([^']*)'",
        output, re.MULTILINE,
    )
    labels = re.findall(r"^application-label:'([^']+)'$", output, re.MULTILINE)
    activities = re.findall(r"^launchable-activity: name='([^']+)'", output, re.MULTILINE)
    if len(packages) != 1 or len(labels) != 1 or len(activities) != 1:
        raise ValueError("APK package/version/label metadata is missing or ambiguous")
    package, code, version = packages[0]
    if not 0 < int(code) < 2**31:
        raise ValueError("APK versionCode is invalid")
    return {
        "package": package,
        "versionCode": int(code),
        "versionName": version,
        "label": labels[0],
        "launchableActivity": activities[0],
    }


def verify_apk(root, sdk):
    root, sdk = Path(root), Path(sdk)
    report_path = root / "android-apk.json"
    report_path.unlink(missing_ok=True)
    source = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    if not re.fullmatch(r"[0-9a-f]{40}", source) or (root / "android-source-sha.txt").read_text().strip() != source:
        raise ValueError("Recorded Android source SHA does not match this checkout")

    apk = root / "android-app/app/build/outputs/apk/debug/app-debug.apk"
    if not apk.is_file():
        raise ValueError("Missing five-layer debug APK")
    tools = sdk / "build-tools" / "34.0.0"
    aapt = str(tools / "aapt")
    metadata = badging(subprocess.check_output([aapt, "dump", "badging", str(apk)], text=True))
    if metadata["package"] != EXPECTED_PACKAGE:
        raise ValueError("Unexpected five-layer applicationId")
    if metadata["label"] != EXPECTED_LABEL:
        raise ValueError("Unexpected five-layer application label")
    if metadata["launchableActivity"] != EXPECTED_ACTIVITY:
        raise ValueError("Unexpected five-layer launcher activity")

    permissions = subprocess.check_output([aapt, "dump", "permissions", str(apk)], text=True)
    manifest = subprocess.check_output([aapt, "dump", "xmltree", str(apk), "AndroidManifest.xml"], text=True)
    for forbidden in ("FOREGROUND_SERVICE", "POST_NOTIFICATIONS", "VIBRATE"):
        if forbidden in permissions:
            raise ValueError(f"Chart Pro permission remains in APK: {forbidden}")
    if "StrategyMonitorService" in manifest:
        raise ValueError("Chart Pro StrategyMonitorService remains in APK")

    with zipfile.ZipFile(apk) as archive:
        dex_names = [name for name in archive.namelist() if re.fullmatch(r"classes(?:[0-9]+)?\.dex", name)]
        if not dex_names:
            raise ValueError("APK has no DEX payload")
        dex = b"".join(archive.read(name) for name in dex_names)
    leaked = [marker.decode("ascii") for marker in FORBIDDEN_DEX_MARKERS if marker in dex]
    if leaked:
        raise ValueError(f"Chart Pro classes remain in APK DEX: {leaked}")

    signature = subprocess.check_output(
        [str(tools / "apksigner"), "verify", "--verbose", "--print-certs", str(apk)], text=True
    )
    signers = re.findall(
        r"^Signer #\d+ certificate SHA-256 digest: ([0-9a-fA-F]{64})$",
        signature, re.MULTILINE,
    )
    if not signers:
        raise ValueError("Missing verified APK signing certificate")

    target = root / "artifacts" / f"BTCUSDT-Quant-System-Paper-{source[:12]}.apk"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(apk, target)
    entry = {
        **metadata,
        "certificateSha256": sorted(set(value.lower() for value in signers)),
        "sha256": hashlib.sha256(apk.read_bytes()).hexdigest(),
        "bytes": apk.stat().st_size,
        "artifact": str(target.relative_to(root)),
        "chartProDexMarkers": [],
        "manifestServiceIsolation": "PASS",
        "permissionsIsolation": "PASS",
    }
    report = {"sourceSha": source, "variant": "debug", "mode": "PAPER_ONLY", "apk": entry}
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return report


if __name__ == "__main__":
    result = verify_apk(os.environ["CM_BUILD_DIR"], os.environ["ANDROID_SDK_ROOT"])
    print("Verified five-layer-only APK for source", result["sourceSha"])
