# Gemini Tasks in delegateH

Use Gemini for Mac signed in to the intended personal Google AI Pro account. Google also lists Tasks for eligible Ultra accounts. Follow the app’s normal sign-in and consent steps. The Codex handoff uses the Mac app and the signed-in plan. [Google Tasks setup](https://support.google.com/gemini/answer/17208717) · [Gemini model availability](https://support.google.com/gemini/answer/18648722)

## Submit and collect

1. Open Gemini for Mac with the available computer-use tool. Open a new conversation, select **Task**, and select the requested worker model in the picker. Use **4 Hydrogen** by default. Match the request against the model label in the picker, allowing unambiguous forms such as “Argon” for “4 Argon.” If the app omits the model, report the available Task models and wait for the user to choose. If the app requests sign-in or account consent, let the user complete that step.
2. Verify the selection before submitting each prompt. The picker can reset between tasks. Confirm the posted prompt in the new task thread before opening another conversation. Give each independent task its own thread. Record the task ID and thread title or another visible way to find it. Verify each submission before retrying.
3. Reopen the task thread and look for the completion state and final answer. Check the response’s **More actions** menu for the **Used … model** entry. Record the reported model and flag missing metadata. If it reports a different model, discard that result for the selected worker and report the mismatch. The composer picker can change after submission and only shows what is selected for the next prompt.
4. Validate each claim against local evidence. For edits, inspect the proposed diff and reconcile it with the working tree before applying it. Run the actual project checks from Codex.

When computer use is unavailable, provide the prompts and the chosen worker model for the user to submit in **Task** mode. Ask for the final answers and any response model labels. The same review steps apply. To stop a running task, open its thread and use **Stop response**.

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
