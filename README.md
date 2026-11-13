# delegateH

A Codex skill that sends independent tasks to a model you choose in Gemini for Mac. Your active Codex model plans the work, reviews results, integrates accepted changes, and runs checks. The default Gemini worker is 4 Hydrogen.

If Hydrogen is unavailable in Antigravity on your promotional or trial Google AI Pro plan, check Gemini for Mac. This workaround is available when your account offers both **Task** mode and **4 Hydrogen**. [Antigravity plan FAQ](https://antigravity.google/docs/faq) · [Gemini model availability](https://support.google.com/gemini/answer/18648722)

[Read the setup guide](https://hightierroach.github.io/delegateH/)

## Install

You need Codex, Git to clone this repository, and the Gemini app for Mac. Sign in with your personal Google AI Pro account. In Gemini, open a new conversation, choose **Task**, and check that your preferred worker model is available. Complete the app’s Tasks onboarding if prompted. [Download Gemini](https://gemini.google/desktop/)

```sh
git clone https://github.com/HighTierRoach/delegateH.git
cd delegateH
mkdir -p "$HOME/.agents/skills"
test ! -e "$HOME/.agents/skills/delegateH" &&
  cp -R delegateH "$HOME/.agents/skills/"
```

Use a fresh install destination. If the skill is already installed, review your local changes before updating it.

## Choose your models

Select your orchestrator in Codex before invoking the skill. From the CLI, start a session with `codex -m <model-id>`, for example `codex -m gpt-6.1-sol`. Naming an orchestrator in your prompt tells the skill to check the active model. Omit it to use the active model by default.

```text
$delegateH AUTO Use gpt-6.1-sol as orchestrator. Use 4 Argon as the Gemini Tasks worker. Review this change and delegate independent checks if useful.
```

Specify any worker model shown in your Gemini **Task** picker. If you omit the worker, the skill selects 4 Hydrogen. If the chosen model is unavailable, the skill reports the available choices. Requests use the signed-in Gemini plan and its Tasks allowance.

Codex uses computer use to submit tasks and read results in the Mac app. Each task receives scoped prompt context and can return findings or a proposed patch for Codex to verify. If computer use is unavailable, you can submit the prepared prompts manually. [Gemini Tasks workflow](delegateH/references/gemini-tasks.md)

Live Mac handoffs returned structured results with both 4 Hydrogen and 4 Argon, as confirmed by Gemini’s response menu. Antigravity’s CLI and ACP catalogs omitted Hydrogen during the account checks. The existing Antigravity dispatcher remains available for an explicit Antigravity workflow. [Antigravity operations guide](delegateH/references/operations.md)

The Antigravity dispatcher’s local tests require Python 3.9 or newer.

```sh
python3 -B -m unittest discover -s delegateH/tests -v
```
