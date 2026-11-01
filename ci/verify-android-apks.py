#!/usr/bin/env python3
"""Verify the built APK identities before publishing the parallel-install artifact."""

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess


BASE_PACKAGE = "com.kenznguyen.btclivealerts"


def badging(output):
    packages = re.findall(
        r"^package: name='([^']+)' versionCode='([0-9]+)' versionName='([^']*)'", output, re.MULTILINE
    )
    labels = re.findall(r"^application-label:'([^']+)'$", output, re.MULTILINE)
    activities = re.findall(r"^launchable-activity: name='([^']+)'", output, re.MULTILINE)
    if len(packages) != 1 or len(labels) != 1 or len(activities) != 1 or not 0 < int(packages[0][1]) < 2**31:
        raise ValueError("APK package/version/label metadata is missing or ambiguous")
    package, code, version = packages[0]
    return {"package": package, "versionCode": int(code), "versionName": version,
            "label": labels[0], "launchableActivity": activities[0]}


def verify_apks(root, sdk):
    root, sdk = Path(root), Path(sdk)
    report_path = root / "android-apks.json"
    report_path.unlink(missing_ok=True)
    for previous in (root / "artifacts").glob("BTC-5-Tang-Paper-*.apk"):
        previous.unlink()
    source = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    if not re.fullmatch(r"[0-9a-f]{40}", source) or (root / "android-source-sha.txt").read_text().strip() != source:
        raise ValueError("Recorded Android source SHA does not match this checkout")
    target = root / "artifacts" / f"BTC-5-Tang-Paper-{source[:12]}.apk"
    tools = sdk / "build-tools" / "34.0.0"
    variants = (("debug", BASE_PACKAGE, "BTCUSDT Chart Pro"),
                ("parallel", BASE_PACKAGE + ".paper", "BTC 5 Tầng Paper"))
    entries = []
    for variant, expected_package, expected_label in variants:
        apk = root / "android-app/app/build/outputs/apk" / variant / f"app-{variant}.apk"
        if not apk.is_file():
            raise ValueError(f"Missing {variant} APK")
        metadata = badging(subprocess.check_output([str(tools / "aapt"), "dump", "badging", str(apk)], text=True))
        if (metadata["package"] != expected_package or metadata["label"] != expected_label or
                metadata["launchableActivity"] != BASE_PACKAGE + ".MainActivity"):
            raise ValueError(f"Unexpected {variant} application identity")
        signature = subprocess.check_output(
            [str(tools / "apksigner"), "verify", "--verbose", "--print-certs", str(apk)], text=True
        )
        signers = re.findall(r"^Signer #\d+ certificate SHA-256 digest: ([0-9a-fA-F]{64})$", signature, re.MULTILINE)
        if not signers:
            raise ValueError(f"Missing verified {variant} signing certificate")
        entries.append({"variant": variant, **metadata, "certificateSha256": sorted(set(value.lower() for value in signers)),
                        "sha256": hashlib.sha256(apk.read_bytes()).hexdigest(), "bytes": apk.stat().st_size,
                        "artifact": str(apk.relative_to(root))})
    regular, parallel = entries
    if parallel["versionCode"] != regular["versionCode"] or parallel["versionName"] != regular["versionName"] + "-paper":
        raise ValueError("Parallel APK version does not match the regular build")
    if parallel["certificateSha256"] != regular["certificateSha256"]:
        raise ValueError("Debug and parallel APKs were signed by different certificates")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(root / parallel["artifact"], target)
    parallel["artifact"] = str(target.relative_to(root))
    report = {"sourceSha": source, "signing": "DEBUG", "apks": entries}
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return report


if __name__ == "__main__":
    result = verify_apks(os.environ["CM_BUILD_DIR"], os.environ["ANDROID_SDK_ROOT"])
    print("Verified regular and parallel APK identities for source", result["sourceSha"])
