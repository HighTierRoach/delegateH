---
name: delegateH
description: Coordinate independent 4 Hydrogen tasks in Gemini for Mac from the active GPT-6.1 Sol Codex session. Use for explicit $delegateH requests or complex work that benefits from independent analysis or proposed edits.
---

# delegateH

Use GPT-6.1 Sol (`gpt-6.1-sol`) as coordinator. If the session reports a different model, ask the user to select Sol. Keep planning, review, edits, and testing in Codex.

1. In AUTO, handle straightforward or interdependent work directly. When delegation helps, give each task a distinct objective, task ID, expected evidence, and only the authorized context it needs. Honor explicit modes and counts. Use up to three independent tasks by default and cap a round at five.
2. Read [Gemini Tasks](references/gemini-tasks.md) and submit each task in a separate conversation in the signed-in Gemini for Mac app. Select **Task** and verify **4 Hydrogen** before submitting. Use Codex computer use when available. Otherwise hand the user the prepared prompts for manual submission. Use this Gemini Tasks path for ordinary invocations. The [Antigravity workflow](references/operations.md) is reserved for an explicit request to use that integration.
3. In BUILD request proposed edits. In DEBUG request independent diagnoses. In AUDIT request defensive findings. In TEST request test cases or proposed test edits. In RESEARCH request evidence-backed analysis of supplied sources. Use authorized, sanitized excerpts and keep project folders disconnected for these prompt-based tasks. Gemini returns recommendations or proposed changes, and Codex performs local edits and runs checks.
4. Reopen each task to collect its result. Verify task identity, completion, and the reported model when visible. Review results against local evidence. Apply only accepted changes, preserve existing work, and report any incomplete or unverified tasks.

Examples

- `$delegateH BUILD propose changes for this feature with 3 Hydrogen tasks.`
- `$delegateH AUDIT review this change from two independent angles.`
- `$delegateH TEST this project for edge cases.`
