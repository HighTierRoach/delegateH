# Gemini Tasks in delegateH

Use Gemini for Mac signed in to the intended personal Google AI Pro account. Google also lists Tasks for eligible Ultra accounts. Follow the app’s normal sign-in and consent steps. The Codex handoff uses the Mac app and the signed-in plan. [Google Tasks setup](https://support.google.com/gemini/answer/17208717) · [Gemini model availability](https://support.google.com/gemini/answer/18648722)

## Submit and collect

1. Open Gemini for Mac with the available computer-use tool. Open a new conversation, select **Task**, then check the model picker for **4 Hydrogen**. Select it when needed. If the app requests sign-in or account consent, let the user complete that step.
2. Paste one prompt and submit it. Confirm the posted prompt in the new task thread before opening another conversation. Give each independent task its own thread. Record the task ID and thread title or another visible way to find it. Verify each submission before retrying.
3. Reopen the task thread and look for the completion state and final answer. The response’s **More actions** menu may show **Used 4 Hydrogen model**. Treat that indicator as confirmation when present. Record only the relevant result and flag any incomplete tasks or model you could not verify.
4. Validate each claim against local evidence. For edits, inspect the proposed diff and reconcile it with the working tree before applying it. Run the actual project checks from Codex.

When computer use is unavailable, provide the prepared prompts for the user to submit in **Task** mode and collect the answers they return. The same review steps apply. To stop a running task, open its thread and use **Stop response**.

## Prompt template

```text
Task ID: <unique ID>
Objective: <one independent outcome>
Context: <authorized and sanitized excerpts>
Constraints: Work only from the supplied context. Do not use tools, files, web, or connected apps.
Expected evidence: <paths, observed facts, or test cases that substantiate the result>
Return a JSON object with task_id, status (completed or blocked), findings, and evidence.
If changes are appropriate, include a proposed unified diff. List checks Codex should run.
```

Treat JSON and diffs as model output. Validate the task ID and parse the JSON when the prompt requires it. Ask for a corrected answer when it is incomplete or malformed. Keep files, web, and connected apps outside a prompt-only task. Gemini Tasks runs through the app and reports completion there. Its quota, session controls, and response format follow the app. [Google Tasks usage and limits](https://support.google.com/gemini/answer/17094507?co=GENIE.Platform%3DDesktop&hl=en)
