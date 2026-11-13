---
name: delegateH
description: Coordinate independent Gemini Tasks on Mac from the active Codex session. Choose a Gemini worker model such as 4 Hydrogen or 4 Argon. Use for explicit $delegateH requests or complex work that benefits from independent analysis or proposed edits.
---

# delegateH

The active Codex model coordinates and owns planning, review, edits, and testing. If the request names an orchestrator, verify it against the active session model using session metadata, the Codex model picker, or the user’s explicit confirmation of the active model. A requested name or an entry in the model catalog alone does not establish the active model. If the model differs or cannot be confirmed, ask the user to select or confirm it before proceeding. The skill runs in the current session. Users select its model in Codex or start it with `codex -m <model-id>`.

1. In AUTO, handle straightforward or interdependent work directly. When delegation helps, give each task a distinct objective, task ID, expected evidence, and only the authorized context it needs. Honor explicit modes and counts. Use up to three independent tasks by default and cap a round at five.
2. Use the requested Gemini worker model, defaulting to **4 Hydrogen**. Read [Gemini Tasks](references/gemini-tasks.md) and verify the selection in **Task** mode for each new conversation before submitting. If the chosen worker is unavailable, report the picker options and wait for the user to choose. Use Codex computer use when available. Otherwise give the user the prepared prompts and the chosen model for manual submission. The [Antigravity workflow](references/operations.md) is reserved for an explicit request to use that integration.
3. In BUILD request proposed edits. In DEBUG request independent diagnoses. In AUDIT request defensive findings. In TEST request test cases or proposed test edits. In RESEARCH request evidence-backed analysis of supplied sources. Use authorized, sanitized excerpts and keep project folders disconnected for these prompt-based tasks. Gemini returns recommendations or proposed changes, and Codex performs local edits and runs checks.
4. Reopen each task to collect its result. Verify task identity, completion, and the reported model when visible. Flag missing model evidence and reject results that report a different model. Review results against local evidence. Apply only accepted changes, preserve existing work, and report any incomplete or unverified tasks.

Examples

- `$delegateH BUILD propose changes for this feature with 3 Hydrogen tasks.`
- `$delegateH AUDIT use gpt-6.1-sol as orchestrator and 4 Argon as the Gemini Tasks worker. Review this change from two independent angles.`
- `$delegateH TEST this project for edge cases.`
