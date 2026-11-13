"""Antigravity CLI transport. Persist only selected, redacted result fields."""

import asyncio
import json
import os
import re
import signal
from pathlib import Path

SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["completed", "blocked"]},
        "summary": {"type": "string"},
        "evidence": {"type": "array", "items": {"type": "string"}},
        "checks": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["status", "summary", "evidence", "checks"],
}

USAGE_KEYS = ("input_tokens", "output_tokens", "thinking_tokens",
              "cache_read_tokens", "total_tokens")
SENSITIVE = re.compile(
    r"(?i)(?:\b(?:bearer\s+\S+|(?:[\w-]+[_-])?(?:api[-_ ]?key|access[-_ ]?token|refresh[-_ ]?token|"
    r"password|secret)\s*[:=]\s*[\"']?\S+)|\b(?:ya29\.|AIza|gh[pousr]_|github_pat_|"
    r"sk-|xox[baprs]-)[\w.\-]{8,}|-----BEGIN [A-Z ]*PRIVATE KEY-----)"
)
LOGIN_LINK = re.compile(r"https?://\S*(?:[?&](?:code|token|state|code_challenge)=)\S*", re.I)
DENIED = re.compile(r"(?i)permission (?:denied|required)|requires (?:user )?approval|"
                    r"not allowed in headless|soft.denied|blocked by (?:policy|permission)")


def child_env():
    names = ("PATH", "HOME", "USER", "LOGNAME", "LANG", "LC_ALL", "LC_CTYPE",
             "TMPDIR", "SSL_CERT_FILE", "SSL_CERT_DIR", "XDG_CONFIG_HOME")
    return {name: os.environ[name] for name in names if name in os.environ}


def settings(writable=False):
    denied = ["command(*)", "mcp(*)", "execute_url(*)", "read_url(*)",
              "read_file(.git)", "write_file(.git)"]
    if not writable:
        denied.append("write_file(*)")
    config = Path.home() / ".gemini/antigravity-cli/settings.json"
    existing = json.loads(config.read_text(encoding="utf-8")) if config.exists() else {}
    permissions = existing.get("permissions", {})
    return json.dumps({
        "modelProvider": "", "useG1Credits": False, "allowNonWorkspaceAccess": False,
        "enableTerminalSandbox": True,
        "toolPermission": "strict" if existing.get("toolPermission") == "strict" else "request-review",
        "permissions": {"deny": denied + permissions.get("deny", []),
                        "ask": permissions.get("ask", []), "allow": []},
    }, separators=(",", ":"))


async def bounded_read(reader, limit):
    data = bytearray()
    while True:
        chunk = await reader.read(16384)
        if not chunk:
            return bytes(data).decode("utf-8", errors="replace")
        data.extend(chunk)
        if len(data) > limit:
            raise ValueError("Provider output exceeded the configured capture limit")


async def stop_process(proc):
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    await asyncio.sleep(0.3)
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    await proc.wait()


async def capture(argv, cwd, timeout, payload=None, started=None):
    launch = asyncio.create_task(asyncio.create_subprocess_exec(
        *map(str, argv), cwd=cwd, env=child_env(), start_new_session=True,
        stdin=asyncio.subprocess.PIPE if payload is not None else asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
    ))
    proc = None
    async def send():
        if payload is None:
            return
        try:
            proc.stdin.write(payload)
            await proc.stdin.drain()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            proc.stdin.close()

    try:
        proc = await asyncio.shield(launch)
        if started:
            started(proc.pid)
        transfers = asyncio.gather(
            bounded_read(proc.stdout, 8 * 1024 * 1024),
            bounded_read(proc.stderr, 256 * 1024),
            send(), proc.wait(),
        )
        out, err, _, code = await asyncio.wait_for(transfers, timeout)
        return code, out, err
    except BaseException:
        if proc is None and not launch.cancelled():
            try:
                proc = await launch
            except OSError:
                pass
        if proc is not None:
            try:
                # Closing the pipes releases subprocess waiters even when an
                # escaped descendant still holds a write end.
                for stream in (proc.stdout, proc.stderr):
                    stream._transport.close()
                await asyncio.wait_for(stop_process(proc), 3)
            except asyncio.TimeoutError:
                pass
        raise


def failure_kind(message):
    message = message.lower()
    if re.search(r"invalid model|unknown model|model.*not (recognized|available|found)|model.*access", message):
        return "model_unavailable"
    if re.search(r"\b401\b|unauthenticated|sign[- ]?in|\blogin\b|authenticat|oauth", message):
        return "authentication"
    if re.search(r"\b429\b|rate.?limit|quota|resource.?exhausted|\boverage\b|\bcredits\b", message):
        return "quota"
    if DENIED.search(message) or "403" in message:
        return "permission"
    if re.search(r"\b(502|503|504)\b|service unavailable|connection reset|temporary failure", message):
        return "transient"
    return "provider_error"


def clean(value, limit):
    if not isinstance(value, str):
        return ""
    if SENSITIVE.search(value):
        return "[redacted credential-like content]"
    return LOGIN_LINK.sub("[redacted authorization link]", value)[:limit]


def catalog_has(stdout, model):
    return any(line.split(maxsplit=1)[0] == model for line in stdout.splitlines() if line.strip())


def interpret(code, stdout, stderr, model, cwd):
    init = []
    terminal = []
    permission_denied = bool(DENIED.search(stderr))
    delegated = False
    for line in stdout.splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
            if not isinstance(event, dict):
                raise ValueError
        except ValueError:
            return {"status": "invalid_output"}
        kind = event.get("event")
        if kind == "init":
            init.append(event.get("init"))
        elif kind == "result":
            terminal.append(event.get("result"))
        elif kind == "step_update":
            step = event.get("step_update")
            if not isinstance(step, dict):
                continue
            delegated |= bool(step.get("subagent_info")) or step.get("tool_name") == "invoke_subagent"
            tool = step.get("tool_info")
            error = tool.get("error") if isinstance(tool, dict) else None
            permission_denied |= bool(error and DENIED.search(str(error)))

    result = terminal[0] if len(terminal) == 1 else None
    if not isinstance(result, dict):
        return {"status": failure_kind(stderr) if code else "invalid_output"}
    provider_status = result.get("status")
    usage = result.get("usage")
    output = {"provider_status": provider_status if isinstance(provider_status, str) and provider_status in {
        "SUCCESS", "ERROR", "CANCELED", "INTERRUPTED", "INVALID", "WAITING", "RUNNING"
    } else "UNKNOWN", "exit_code": code}
    if isinstance(usage, dict):
        output["usage"] = {k: usage[k] for k in USAGE_KEYS
                           if type(usage.get(k)) is int and usage[k] >= 0}
    if code or provider_status != "SUCCESS":
        message = result.get("error")
        output["status"] = {
            "CANCELED": "cancelled", "INTERRUPTED": "cancelled", "WAITING": "incomplete",
        }.get(output["provider_status"], failure_kind(
            (message if isinstance(message, str) else "") + "\n" + stderr))
        return output

    active = init[0] if len(init) == 1 else None
    display = "Gemini 4 Hydrogen (" + model.rsplit("-", 1)[-1].capitalize() + ")"
    if (not isinstance(active, dict) or active.get("model") not in (model, display)
            or active.get("permission_mode") not in ("request-review", "strict")
            or not isinstance(active.get("cwd"), str)
            or Path(active["cwd"]).resolve() != cwd.resolve()):
        return dict(output, status="unverified_session")
    output["reported_model"] = active["model"]
    report = result.get("structured_output")
    if (not isinstance(report, dict) or report.get("status") not in ("completed", "blocked")
            or not isinstance(report.get("summary"), str) or not report["summary"].strip()
            or any(not isinstance(report.get(key), list)
                   or not all(isinstance(value, str) for value in report[key])
                   for key in ("evidence", "checks"))):
        return dict(output, status="invalid_output")
    output["report"] = {
        "status": report["status"], "summary": clean(report["summary"], 4000),
        **{key: [clean(value, 2000) for value in report[key][:24]]
           for key in ("evidence", "checks")},
    }
    if permission_denied:
        return dict(output, status="permission")
    if delegated:
        return dict(output, status="unexpected_delegation")
    if report["status"] == "blocked" or not any(value.strip() for value in report["evidence"]):
        return dict(output, status="incomplete")
    return dict(output, status="candidate")


async def run_worker(agy, model, cwd, prompt, writable, timeout, started):
    argv = [
        agy, "--settings", settings(writable), "--mode", "accept-edits" if writable else "plan",
        "--sandbox", "--disable-slash-commands", "--model", model,
        "--input-format", "stream-json", "--output-format", "stream-json",
        "--json-schema", json.dumps(SCHEMA, separators=(",", ":")), "--log-file", os.devnull,
    ]
    request = {"event": "user", "message": {"content": prompt}}
    payload = (json.dumps(request) + "\n").encode()
    try:
        code, stdout, stderr = await capture(argv, cwd, timeout, payload, started)
        return interpret(code, stdout, stderr, model, cwd)
    except asyncio.TimeoutError:
        return {"status": "timeout"}
    except ValueError:
        return {"status": "invalid_output"}
    except OSError:
        return {"status": "launch_failed"}
