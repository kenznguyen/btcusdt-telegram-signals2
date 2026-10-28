"""Publish Codemagic build assets to versioned GitHub Releases (not git history).

Requires GH_RELEASE_TOKEN with repository Contents:read/write, only on Codemagic.
Fails closed when credentials/assets/API verification are missing.
"""
import argparse
import hashlib
import json
import mimetypes
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API = "https://api.github.com"
MAX_ASSET_BYTES = 250_000_000
KINDS = ("android", "freqtrade", "freqai")


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_build_id(value):
    result = re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip("-.")
    if not result:
        raise ValueError("CM_BUILD_ID missing")
    return result[:100]


def inspect_assets(asset_paths):
    paths, seen = [], set()
    for item in asset_paths:
        path = Path(item)
        if not path.is_file():
            raise FileNotFoundError(f"Required asset missing: {path}")
        size = path.stat().st_size
        if size <= 0 or size > MAX_ASSET_BYTES:
            raise ValueError(f"Asset empty or over 250MB: {path}")
        if path.name in seen:
            raise ValueError(f"Duplicate GitHub asset name: {path.name}")
        paths.append(path)
        seen.add(path.name)
    if not paths:
        raise ValueError("No assets selected")
    return paths


def github_api(url, token, method="GET", body=None, content_type="application/vnd.github+json"):
    headers = {
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "btcusdt-chart-pro-codemagic",
    }
    if body is not None:
        headers["Content-Type"] = content_type
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            raw = response.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        # Never print Authorization or HTTP response bodies containing details.
        raise RuntimeError(f"GitHub HTTP {exc.code}: {method} {url.split('?')[0]}") from None


def publish(repository, kind, commit, build_id, token, asset_paths):
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", repository):
        raise ValueError("Invalid repository name")
    if kind not in KINDS:
        raise ValueError("Invalid publish kind")
    if not re.fullmatch(r"[0-9a-fA-F]{7,40}", commit):
        raise ValueError("CM_COMMIT must be a commit SHA")
    if not token:
        raise ValueError("GH_RELEASE_TOKEN is missing (Codemagic secret required)")
    assets = inspect_assets(asset_paths)
    tag = f"chart-pro/{kind}/{safe_build_id(build_id)}"
    checksums = {p.name: {"sha256": sha256(p), "bytes": p.stat().st_size} for p in assets}
    description = (
        "Codemagic output — backtest/research or Android Debug, no live trading.\n\n"
        f"Commit: {commit}\nBuild: {build_id}\nCategory: {kind}\n\n"
        "Not a profitability guarantee. Funding/liquidation/parity are not "
        "certified by publishing this release."
    )
    endpoint = f"{API}/repos/{repository}"
    payload = json.dumps({
        "tag_name": tag, "target_commitish": commit,
        "name": f"BTCUSDT Chart Pro {kind} {safe_build_id(build_id)}",
        "body": description, "draft": False, "prerelease": True,
    }).encode("utf-8")
    release = github_api(endpoint + "/releases", token, "POST", payload)
    upload_url = release["upload_url"].split("{")[0]
    uploaded = []
    for path in assets:
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        url = upload_url + "?" + urllib.parse.urlencode({"name": path.name})
        result = github_api(url, token, "POST", path.read_bytes(), mime)
        if result.get("state") != "uploaded":
            raise RuntimeError(f"GitHub did not confirm upload: {path.name}")
        uploaded.append({"name": path.name, "url": result.get("browser_download_url"),
                         **checksums[path.name]})
    return {
        "published_at_utc": datetime.now(timezone.utc).isoformat(),
        "release_url": release["html_url"], "tag": tag,
        "source_commit": commit, "codemagic_build_id": build_id,
        "kind": kind, "assets": uploaded,
        "github_release_publish_verified": True,
        "real_orders": False, "strategy_engine_parameters_changed": False,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repository", default="kenznguyen/btcusdt-telegram-signals2")
    p.add_argument("--kind", required=True, choices=KINDS)
    p.add_argument("--commit", default=os.environ.get("CM_COMMIT", ""))
    p.add_argument("--build-id", default=os.environ.get("CM_BUILD_ID", ""))
    p.add_argument("--asset", action="append", required=True)
    p.add_argument("--manifest", type=Path, required=True)
    args = p.parse_args()
    report = publish(args.repository, args.kind, args.commit, args.build_id,
                     os.environ.get("GH_RELEASE_TOKEN", ""), args.asset)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("GitHub Release:", report["release_url"])
    print("Assets uploaded:", len(report["assets"]))


if __name__ == "__main__":
    sys.exit(main())
