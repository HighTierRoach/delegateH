# delegateH

A Codex skill that sends independent tasks to 4 Hydrogen in Gemini for Mac. GPT-6.1 Sol plans the work, reviews results, integrates accepted changes, and runs checks.

If Hydrogen is unavailable in Antigravity on your promotional or trial Google AI Pro plan, check Gemini for Mac. This workaround is available when your account offers both **Task** mode and **4 Hydrogen**. [Antigravity plan FAQ](https://antigravity.google/docs/faq) · [Gemini model availability](https://support.google.com/gemini/answer/18648722)

[Read the setup guide](https://hightierroach.github.io/delegateH/)

## Install

You need Codex with `gpt-6.1-sol`, Git to clone this repository, and the [Gemini app for Mac](https://gemini.google/desktop/). Sign in with your personal Google AI Pro account. In Gemini, open a new conversation, choose **Task**, and check that **4 Hydrogen** is available. Complete the app’s Tasks onboarding if prompted.

```sh
git clone https://github.com/HighTierRoach/delegateH.git
cd delegateH
mkdir -p "$HOME/.agents/skills"
test ! -e "$HOME/.agents/skills/delegateH" &&
  cp -R delegateH "$HOME/.agents/skills/"
```

Use a fresh install destination. If the skill is already installed, review your local changes before updating it. Start a Codex session with GPT-6.1 Sol selected and enter:

```text
$delegateH AUTO review this change and delegate independent checks if useful.
```

Codex uses computer use to submit tasks and read results in the Mac app. Each task receives scoped prompt context and can return findings or a proposed patch for Codex to verify. If computer use is unavailable, you can submit the prepared prompts manually. [Gemini Tasks workflow](delegateH/references/gemini-tasks.md)

A live Mac handoff returned the expected structured result, and Gemini’s response menu confirmed 4 Hydrogen. Antigravity’s CLI and ACP catalogs omitted Hydrogen during the same account checks. The existing Antigravity dispatcher remains available for an explicit Antigravity workflow. [Antigravity operations guide](delegateH/references/operations.md)

The Antigravity dispatcher’s local tests require Python 3.9 or newer.

```sh
python3 -B -m unittest discover -s delegateH/tests -v
```
