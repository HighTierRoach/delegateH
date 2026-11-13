"""Inspect Antigravity's ACP catalog without submitting a prompt."""

import asyncio
import json
import os
import re

from worker import child_env, failure_kind, stop_process

MAX_LINE = 1024 * 1024
MAX_MESSAGES = 256
MODEL_ID = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_.:/-]{0,127}")


class ACPError(ValueError):
    def __init__(self, status):
        self.status = status
        super().__init__(status)


class Connection:
    def __init__(self, process):
        self.process = process
        self.request_id = 0

    async def send(self, message):
        wire = json.dumps({"jsonrpc": "2.0", **message}) + "\n"
        self.process.stdin.write(wire.encode("utf-8"))
        await self.process.stdin.drain()

    async def request(self, method, params):
        self.request_id += 1
        await self.send({"id": self.request_id, "method": method, "params": params})
        for _ in range(MAX_MESSAGES):
            line = await self.process.stdout.readline()
            if not line:
                raise ACPError("acp_disconnected")
            message = json.loads(line)
            if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
                raise ACPError("acp_invalid_output")
            if "method" in message:
                if "id" in message:
                    await self.send({
                        "id": message["id"],
                        "error": {"code": -32601, "message": "Catalog checks provide no client tools."},
                    })
                continue
            if message.get("id") != self.request_id:
                continue
            if "error" in message:
                error = message["error"]
                if isinstance(error, dict):
                    if error.get("code") == -32000:
                        raise ACPError("authentication")
                    raise ACPError(failure_kind(str(error.get("message", ""))))
                raise ACPError("acp_invalid_output")
            if isinstance(message.get("result"), dict):
                return message["result"]
            raise ACPError("acp_invalid_output")
        raise ACPError("acp_invalid_output")


def model_ids(session):
    legacy = session.get("models") or {}
    items = legacy.get("availableModels")
    if items is not None:
        values = (option.get("modelId") for option in items)
    else:
        selector = next((option for option in session.get("configOptions", [])
                         if option.get("category") == "model"), {})
        options = selector.get("options")
        if options is None:
            raise ACPError("acp_invalid_output")
        values = (option.get("value") for group in options
                  for option in group.get("options", [group]))
    return sorted({value for value in values if isinstance(value, str) and MODEL_ID.fullmatch(value)})


async def inspect_session(connection, cwd, pinned):
    init = await connection.request("initialize", {
        "protocolVersion": 1,
        "clientCapabilities": {},
        "clientInfo": {"name": "delegateH", "version": "0.1.0"},
    })
    if init.get("protocolVersion") != 1:
        raise ACPError("unsupported_acp")
    capabilities = init.get("agentCapabilities", {})
    sessions = capabilities.get("sessionCapabilities", {})
    session = await connection.request("session/new", {"cwd": str(cwd.resolve()), "mcpServers": []})
    session_id = session.get("sessionId")
    if not isinstance(session_id, str) or not session_id:
        raise ACPError("acp_invalid_output")
    try:
        available = model_ids(session)
    finally:
        if "close" in sessions:
            await connection.request("session/close", {"sessionId": session_id})
    return {
        "status": "listed" if pinned in available else "model_unavailable",
        "protocol_version": 1,
        "available_models": available,
        "supports_resume": "resume" in sessions,
        "supports_load": capabilities.get("loadSession") is True or "load" in sessions,
        "session_closed": "close" in sessions,
    }


async def check_catalog(agy, cwd, pinned):
    launch = asyncio.create_task(asyncio.create_subprocess_exec(
        str(agy), "acp", "--sandbox", "--log-file", os.devnull,
        cwd=cwd, env=child_env(), start_new_session=True, limit=MAX_LINE,
        stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    ))
    try:
        process = await asyncio.shield(launch)
    except asyncio.CancelledError:
        try:
            process = await launch
        except OSError:
            pass
        else:
            await close_process(process)
        raise
    except OSError:
        return {"status": "launch_failed"}
    try:
        return await asyncio.wait_for(inspect_session(Connection(process), cwd, pinned), 40)
    except ACPError as error:
        return {"status": error.status}
    except asyncio.TimeoutError:
        return {"status": "timeout"}
    except (AttributeError, TypeError, ValueError):
        return {"status": "acp_invalid_output"}
    except (ConnectionError, OSError):
        return {"status": "acp_disconnected"}
    finally:
        await close_process(process)


async def close_process(process):
    process.stdin.close()
    try:
        await asyncio.wait_for(process.wait(), 1)
    except asyncio.TimeoutError:
        # A peer can leave unread data in the stdout pipe after the deadline.
        process.stdout._transport.close()
        await asyncio.wait_for(stop_process(process), 3)
