"""Codemagic dispatch and legacy history/artifact adapter.

POST /builds and artifact downloads follow current official REST docs. History
uses the legacy GET /builds contract documented at codemagic-docs commit
3102fb2 (builds / artefacts / url). It is not silently reinterpreted as v3;
server compatibility and authenticated live calls still need verification.
"""

import json
import http.client
import os
import re
import urllib.error
import urllib.parse
import urllib.request


BASE = "https://api.codemagic.io"
WORKFLOWS = {"telegram-command", "signal-scan", "dashboard-backtest"}
COMMANDS = {"help", "status", "position", "signal", "backtest", "btstatus", "btresult"}
REPORT_NAMES = {"backtest_last_result.json", "backtest_status.json", "backtest_trades.csv",
                "backtest_equity.csv", "backtest_equity_m15.csv"}
MAX_JSON = 2 * 1024 * 1024
MAX_ARTIFACT = 8 * 1024 * 1024


class CodemagicError(RuntimeError):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


OPENER = urllib.request.build_opener(NoRedirect())


def configured():
    return all(os.environ.get(name, "").strip() for name in ("CODEMAGIC_API_TOKEN", "CODEMAGIC_APP_ID"))


def _configuration():
    if not configured():
        raise CodemagicError("Codemagic is not configured")
    token = os.environ["CODEMAGIC_API_TOKEN"].strip()
    app_id = os.environ["CODEMAGIC_APP_ID"].strip()
    branch = os.environ.get("CODEMAGIC_BRANCH", "main").strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", app_id) or not branch or len(branch) > 200:
        raise CodemagicError("Invalid Codemagic configuration")
    return token, app_id, branch


def _json_request(method, path, payload=None):
    token, _, _ = _configuration()
    request = urllib.request.Request(BASE + path, method=method,
        data=json.dumps(payload, allow_nan=False).encode() if payload is not None else None,
        headers={"x-auth-token": token, "Accept": "application/json", "Content-Type": "application/json"})
    try:
        with OPENER.open(request, timeout=15) as response:
            data = response.read(MAX_JSON + 1)
        if len(data) > MAX_JSON:
            raise ValueError("Oversized response")
        result = json.loads(data)
        if not isinstance(result, dict):
            raise ValueError("Invalid response")
        return result
    except (OSError, http.client.HTTPException, ValueError, TypeError) as exc:
        raise CodemagicError("Codemagic request failed") from None


def start_build(workflow_id, variables=None):
    _, app_id, branch = _configuration()
    if workflow_id not in WORKFLOWS:
        raise CodemagicError("Unsupported workflow")
    variables = variables or {}
    if workflow_id == "telegram-command":
        if set(variables) != {"TELEGRAM_COMMAND"} or variables["TELEGRAM_COMMAND"] not in COMMANDS:
            raise CodemagicError("Unsupported Telegram command")
    elif workflow_id == "dashboard-backtest":
        if set(variables) != {"BACKTEST_DAYS", "BACKTEST_INITIAL_CAPITAL", "ENTRY_MARGIN_PCT", "DCA_MARGIN_RATIO"}:
            raise CodemagicError("Invalid backtest parameters")
    elif variables:
        raise CodemagicError("Scanner does not accept runtime variables")
    if any(not isinstance(value, str) or len(value) > 100 for value in variables.values()):
        raise CodemagicError("Invalid workflow variables")
    payload = {"appId": app_id, "workflowId": workflow_id, "branch": branch}
    if variables:
        payload["environment"] = {"variables": variables}
    result = _json_request("POST", "/builds", payload)
    build_id = result.get("buildId")
    if not isinstance(build_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", build_id):
        raise CodemagicError("Invalid Codemagic build response")
    return build_id


def list_builds(workflow_id, limit=15):
    _, app_id, branch = _configuration()
    if workflow_id not in WORKFLOWS or type(limit) is not int or not 1 <= limit <= 30:
        raise CodemagicError("Invalid history query")
    query = urllib.parse.urlencode({"appId": app_id, "workflowId": workflow_id, "branch": branch})
    result = _json_request("GET", "/builds?" + query)
    builds = result.get("builds")
    if not isinstance(builds, list) or len(builds) > 1000:
        raise CodemagicError("Unsupported Codemagic history response")
    selected = []
    for build in builds:
        if not isinstance(build, dict):
            raise CodemagicError("Invalid build metadata")
        if any(not isinstance(build.get(key), str) for key in ("_id", "appId", "workflowId", "branch", "status")):
            raise CodemagicError("Unsupported build metadata")
        if build.get("appId") != app_id or build.get("workflowId") != workflow_id or build.get("branch") != branch:
            continue
        if not isinstance(build.get("_id"), str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", build["_id"]):
            raise CodemagicError("Invalid build identifier")
        selected.append(build)
    return sorted(selected, key=lambda build: str(build.get("startedAt") or ""), reverse=True)[:limit]


def normalize_build(build):
    _, app_id, _ = _configuration()
    raw_status = build.get("status")
    if not isinstance(raw_status, str):
        raise CodemagicError("Invalid build status")
    final = {"finished": "success", "failed": "failure", "canceled": "cancelled", "timeout": "timed_out", "skipped": "skipped"}
    status = "completed" if raw_status in final else "queued" if raw_status in {"queued", "initializing"} else "in_progress"
    if raw_status not in final and raw_status not in {"queued", "initializing", "preparing", "fetching", "testing", "building", "publishing", "finishing", "warning"}:
        status = "unknown"
    return {"id": build["_id"], "name": build.get("workflowId"), "display_title": build.get("workflowId"),
            "status": status, "conclusion": final.get(raw_status), "created_at": build.get("startedAt"),
            "updated_at": build.get("finishedAt") or build.get("startedAt"),
            "html_url": f"https://codemagic.io/app/{app_id}/build/{build['_id']}"}


def _artifact_url(url):
    if not isinstance(url, str) or len(url) > 8192:
        raise CodemagicError("Invalid artifact URL")
    try:
        parsed = urllib.parse.urlsplit(url)
        port = parsed.port
    except ValueError as exc:
        raise CodemagicError("Invalid artifact URL") from exc
    if parsed.scheme != "https" or parsed.username or parsed.password or parsed.fragment or port not in (None, 443):
        raise CodemagicError("Invalid artifact URL")
    host = parsed.hostname or ""
    if host == "api.codemagic.io":
        path = urllib.parse.unquote(parsed.path)
        if not path.startswith("/artifacts/") or ".." in path.split("/"):
            raise CodemagicError("Invalid artifact path")
        return True
    if host == "storage.googleapis.com" or re.fullmatch(r"[a-z0-9.-]+\.s3(?:[.-][a-z0-9-]+)*\.amazonaws\.com", host) or re.fullmatch(r"[a-z0-9-]+\.blob\.core\.windows\.net", host):
        return False
    raise CodemagicError("Untrusted artifact host")


def download_artifact(url):
    token, _, _ = _configuration()
    # Initial authenticated URL must come from Codemagic, not an arbitrary CDN.
    if not _artifact_url(url):
        raise CodemagicError("Artifact must originate at Codemagic")
    for attempt in range(4):
        authenticated = _artifact_url(url)
        request = urllib.request.Request(url, headers={"x-auth-token": token} if authenticated else {})
        try:
            with OPENER.open(request, timeout=20) as response:
                data = response.read(MAX_ARTIFACT + 1)
            if len(data) > MAX_ARTIFACT:
                raise ValueError("Oversized artifact")
            return data.decode("utf-8-sig")
        except urllib.error.HTTPError as exc:
            if exc.code in {301, 302, 303, 307, 308} and exc.headers.get("Location") and attempt < 3:
                url = urllib.parse.urljoin(url, exc.headers["Location"])
                continue
            raise CodemagicError("Could not download Codemagic artifact") from None
        except (OSError, http.client.HTTPException, ValueError) as exc:
            raise CodemagicError("Could not download Codemagic artifact") from None
    raise CodemagicError("Artifact redirect limit exceeded")


def latest_report(workflow_id="dashboard-backtest"):
    for build in list_builds(workflow_id):
        if build.get("status") != "finished":
            continue
        artifacts = build.get("artefacts", [])
        if not isinstance(artifacts, list):
            raise CodemagicError("Unsupported artifact metadata")
        files = {}
        for artifact in artifacts:
            if not isinstance(artifact, dict):
                raise CodemagicError("Invalid artifact metadata")
            name = artifact.get("name", "")
            if not isinstance(name, str):
                raise CodemagicError("Invalid artifact name")
            canonical = name.removeprefix("dashboard_")
            if canonical not in REPORT_NAMES:
                continue
            if canonical in files:
                raise CodemagicError("Duplicate report artifact")
            files[canonical] = download_artifact(artifact.get("url"))
        if "backtest_last_result.json" not in files:
            continue
        try:
            report = json.loads(files["backtest_last_result.json"])
            status = json.loads(files.get("backtest_status.json", "{}"))
            if not isinstance(report, dict) or not isinstance(status, dict):
                raise ValueError("Invalid report")
            if status.get("run_id") and report.get("run_id") != status["run_id"]:
                raise ValueError("Mixed report runs")
        except (ValueError, TypeError) as exc:
            raise CodemagicError("Invalid backtest report artifacts") from exc
        return {"ok": True, "available": True, "run": normalize_build(build),
                "artifact": {"name": workflow_id + "-report", "created_at": build.get("finishedAt")}, "files": files}
    return {"ok": True, "available": False, "message": "Chưa có báo cáo backtest hợp lệ trong các lần chạy Codemagic gần đây."}
