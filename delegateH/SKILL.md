---
name: delegateH
description: Coordinate independent Gemini 4 Hydrogen workers through Google Antigravity from the active GPT-6.1 Sol Codex session. Use for explicit $delegateH requests or complex build, debug, audit, test, or research tasks that clearly benefit from independent Hydrogen work.
---

# delegateH

Use the active GPT-6.1 Sol (`gpt-6.1-sol`) Codex session as coordinator. Verify the active session model when available. If it differs or cannot be confirmed, tell the user and request that they select Sol before delegating. Antigravity workers are separate local processes. Keep planning, review, integration, testing, and final decisions in this session.

1. Read the user's request and inspect the project, working changes, and relevant instructions. In AUTO, handle straightforward or interdependent work directly. For independent work, identify the objective, expected evidence, allowed files, and constraints for each worker. Honor explicit modes and counts. Default to three useful tasks and cap the round at five or a lower configured limit.
2. Read [operations](references/operations.md) for the manifest and review commands. Run the healthcheck before delegation. The exact Hydrogen slug must be in the account catalog. Report model, subscription, quota, or auth blockers and proceed with locally supported work within the user's scope. Preserve the pinned models.
3. Use BUILD for edits, DEBUG for independent diagnoses, AUDIT for independent defensive, correctness, reliability, architecture, or performance reviews, TEST for coverage or regression work, and RESEARCH for evidence-based investigations. Provide research sources or excerpts when worker web access is unavailable. Assign distinct writable paths. Include only the committed files and sanitized context each worker needs. Treat the manifest and explicitly shared files as content sent to Google's subscription service. Keep secrets, private data, and uncommitted work out of the handoff.
4. Run the manifest with the local dispatcher. Keep the process supervised and monitor its JSON events and summary. A candidate is ready for review. Verify its evidence and diff, compare with the original tree, and request a revision as a new round when useful.
5. Inspect all accepted patches and check applicability in the original tree. Resolve conflicts explicitly while preserving existing staged, unstaged, and untracked work. Apply only reviewed edits and run the actual project checks. Clean up reviewed runs and report the model, worker count, verified results, and unresolved failures.

Examples

- `$delegateH BUILD this feature using 3 Hydrogen workers.`
- `$delegateH Use AUDIT mode with maximum parallelism.`
- `$delegateH TEST this project for edge cases.`
