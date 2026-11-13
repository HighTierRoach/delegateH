# Operating delegateH

Use Python 3.9 or later, Git, and Google’s official macOS Antigravity CLI. The installed script looks for `~/.local/bin/agy` first and then on PATH.

```sh
delegateH_runner="$HOME/.agents/skills/delegateH/scripts/orchestrator.py"
python3 "$delegateH_runner" healthcheck
```

A `listed` healthcheck means the exact model appears in the current account catalog. Run `healthcheck --probe` to verify a minimal live response from the pinned model after login or a provider change. It consumes subscription quota only when the model is listed. Configure the documented Hydrogen reasoning-level slug, worker cap, timeout, and retry count in [config.json](../config.json). The cap of five is local. Google describes work-based quotas and the CLI may return rate-limit or quota errors. Check `/usage` before a large round. [Google quota and plan docs](https://antigravity.google/docs/plans/).

Codex needs command access to the installed Antigravity CLI, network and local account authentication, and write access to its temp directory and `~/.local/state/delegateH` for dispatch. If the current sandbox blocks these, use the session's normal permission request for the specific operation. [Codex permissions docs](https://learn.chatgpt.com/docs/agent-approvals-security).

For personal subscription usage, open `~/.local/bin/agy` interactively if sign-in is required and select the personal Google account with Google AI Pro. Check the selected account and plan in Antigravity. Session overrides select Google account authentication and disable credit overages. The runner passes an allowlisted environment that excludes Gemini API keys and Cloud ADC settings. [Google authentication docs](https://antigravity.google/docs/install/?tab=cli) · [Google credits docs](https://antigravity.google/docs/cli/credits/).

If Hydrogen is absent from `agy models`, use Antigravity’s Models & Usage page to confirm the plan and refresh entitlements. If the picker still shows Hydrogen unavailable, wait for account access or contact Google support. [Google’s Hydrogen rollout announcement](https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-4-hydrogen/).

To inspect the official Agent Client Protocol (ACP) catalog, run:

```sh
python3 "$delegateH_runner" healthcheck --acp
```

This opens an empty sandboxed session using Antigravity’s cached sign-in, reads the advertised model IDs and session capabilities, and closes the session when supported. It submits no inference prompt. Worker dispatch uses headless `agy`. ACP exposes the models available to the signed-in account. [Google’s ACP documentation](https://antigravity.google/docs/ide/extensions/acp/).

## Dispatch a round

Create a private manifest outside the project. Supply one task per worker. `workers` defaults to three and acts as a round ceiling. For five-way parallelism, write five independent tasks and set `workers` to five. Set `share` to literal paths from the committed tree, with directory names accepted for recursive selection. Set `write` to exact file paths. Include an existing writable file in `share`. Use a new path for a new file. Omit both arrays for a prompt-only worker and omit `--repo` if no task needs a project.

```json
{
  "mode": "BUILD",
  "workers": 1,
  "tasks": [
    {
      "id": "normalize",
      "objective": "Normalize trailing whitespace in the formatter output.",
      "context": "Keep the public function signature.",
      "constraints": "Preserve leading whitespace and line endings.",
      "expected": "Update formatter.py and name the cases Sol should test.",
      "share": ["formatter.py", "tests/test_formatter.py"],
      "write": ["formatter.py"]
    }
  ]
}
```

```sh
python3 "$delegateH_runner" run /path/to/private-manifest.json --repo "$PWD"
```

The runner exports approved regular blobs from one committed HEAD into independent Git repositories, one per worker. Each has its own index, objects, refs, and workspace. Uncommitted files, Git history, remotes, symlinks, submodules, common credential paths, and Antigravity workspace customizations stay outside the worker snapshot. Check selected content for embedded secrets. Task manifests and patches can still contain private project content. Antigravity maintains its own conversation records under the signed-in account.

Read-only workers use plan mode. Workers with a write scope use accept-edits for workspace files. Session policy keeps requests for review, denies shell commands, URL access, and MCP tool calls, and preserves personal deny and ask rules. Use Sol to run tests or any command that needs approval, and give research workers independently scoped sources or excerpts. The runner checks for Antigravity global hooks, plugin hooks, and global MCP startup configuration before dispatch. [Google headless and permission docs](https://antigravity.google/docs/cli/headless/).

## Review, revise, and clean up

The initial event prints the run directory under `~/.local/state/delegateH`. Later events report worker starts and terminal states. Read `summary.json` for sanitized structured results, reported model, timestamps, provider status, usage when available, and patch paths. A failed sibling does not invalidate a usable patch. Provider success requires the pinned model in the stream, a terminal result, a valid report with evidence, and any expected in-scope file changes. Sol still has to verify task completion.

Inspect a patch and check applicability with `git apply --check -- /absolute/path/to/worker.patch`. Apply approved changes without `--index` to preserve the staging area. If the check fails, inspect and reconcile the intended changes manually. Run project tests from Sol’s workspace. To request revisions, dispatch a fresh scoped round with verified feedback and a suitable committed base, or include a sanitized excerpt of the prior candidate in its context.

A timeout or cancellation terminates worker process groups. A transient provider failure can retry once within the same deadline if the worker left no changes. Auth, quota, model, permission, and other terminal errors need review. One round at a time runs per user.

```sh
python3 "$delegateH_runner" cleanup run-abcdefgh
python3 "$delegateH_runner" cleanup run-abcdefgh --discard
```

Normal cleanup removes finished clean snapshots. Use `--discard` for a specific reviewed run whose remaining patches, changes, or interrupted snapshots may be deleted. Cleanup is limited to the selected private run directory. After a hard kill, check the reported worker PIDs and process groups for remaining workers before discarding the run. The runner does not persist raw provider logs or full tool traces.

After changing the dispatcher, run `python3 -B -m unittest discover -s "$HOME/.agents/skills/delegateH/tests" -v` for the offline process and Git tests. They use a synthetic provider and create disposable repositories automatically.
