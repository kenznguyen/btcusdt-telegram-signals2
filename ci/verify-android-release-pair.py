#!/usr/bin/env python3
"""Verify regular-release host and parallel/.paper APKs share one release signer."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess


BASE_PACKAGE = "com.kenznguyen.btclivealerts"
EXPECTED_ACTIVITY = BASE_PACKAGE + ".MainActivity"
VARIANTS = (
    ("release", BASE_PACKAGE, "BTCUSDT Chart Pro", "app-release.apk"),
    ("parallel", BASE_PACKAGE + ".paper", "BTC 5 Tầng Paper", "app-parallel.apk"),
)


def badging(output):
    packages = re.findall(
        r"^package: name='([^']+)' versionCode='([0-9]+)' versionName='([^']*)'",
        output,
        re.MULTILINE,
    )
    labels = re.findall(r"^application-label:'([^']+)'$", output, re.MULTILINE)
    activities = re.findall(r"^launchable-activity: name='([^']+)'", output, re.MULTILINE)
    if len(packages) != 1 or len(labels) != 1 or len(activities) != 1:
        raise ValueError("APK package/version/label/activity metadata is missing or ambiguous")
    package, code, version = packages[0]
    if not 0 < int(code) < 2**31:
        raise ValueError("APK versionCode is outside Android's supported positive range")
    return {
        "package": package,
        "versionCode": int(code),
        "versionName": version,
        "label": labels[0],
        "launchableActivity": activities[0],
    }


def certificate_digests(output):
    values = re.findall(
        r"^Signer #\d+ certificate SHA-256 digest: ([0-9a-fA-F]{64})$",
        output,
        re.MULTILINE,
    )
    if not values:
        raise ValueError("APK signer certificate SHA-256 digest is missing")
    return sorted({value.lower() for value in values})


def verify_pair(root, sdk, expected_source_sha):
    root, sdk = Path(root), Path(sdk)
    if not re.fullmatch(r"[0-9a-f]{40}", expected_source_sha):
        raise ValueError("Expected source SHA must be a full 40-character commit SHA")
    actual_source = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
    if actual_source != expected_source_sha:
        raise ValueError("Checkout HEAD does not match the requested source SHA")

    build_tools = sdk / "build-tools" / "34.0.0"
    aapt = build_tools / "aapt"
    apksigner = build_tools / "apksigner"
    if not aapt.is_file() or not apksigner.is_file():
        raise ValueError("Required Android Build Tools 34.0.0 aapt/apksigner are missing")

    entries = []
    for variant, expected_package, expected_label, filename in VARIANTS:
        apk = root / "android-app/app/build/outputs/apk" / variant / filename
        if not apk.is_file() or apk.stat().st_size == 0:
            raise ValueError(f"Missing or empty {variant} APK")
        metadata = badging(
            subprocess.check_output([str(aapt), "dump", "badging", str(apk)], text=True)
        )
        if (
            metadata["package"] != expected_package
            or metadata["label"] != expected_label
            or metadata["launchableActivity"] != EXPECTED_ACTIVITY
        ):
            raise ValueError(f"Unexpected {variant} application identity")
        signature = subprocess.check_output(
            [str(apksigner), "verify", "--verbose", "--print-certs", str(apk)],
            text=True,
        )
        signers = certificate_digests(signature)
        entries.append(
            {
                "variant": variant,
                **metadata,
                "certificateSha256": signers,
                "sha256": hashlib.sha256(apk.read_bytes()).hexdigest(),
                "bytes": apk.stat().st_size,
                "artifact": str(apk.relative_to(root)),
            }
        )

    regular, parallel = entries
    if parallel["versionCode"] != regular["versionCode"]:
        raise ValueError("Regular and parallel APK versionCode values differ")
    if parallel["versionName"] != regular["versionName"] + "-paper":
        raise ValueError("Parallel APK versionName must be regular versionName plus -paper")
    if parallel["certificateSha256"] != regular["certificateSha256"]:
        raise ValueError("Regular host and .paper client APK signer certificates differ")

    return {
        "sourceSha": actual_source,
        "signing": "RELEASE",
        "signerParity": True,
        "apks": entries,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--sdk", required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    result = verify_pair(args.root, args.sdk, args.source_sha)
    Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(
        "Verified regular release host and parallel/.paper APK identities, "
        "matching release signer, and source SHA."
    )


if __name__ == "__main__":
    main()
