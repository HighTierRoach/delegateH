# delegateH

A Codex skill that dispatches independent Gemini 4 Hydrogen tasks through Google's Antigravity CLI. GPT-6.1 Sol stays in charge of planning, reviewing results, integrating changes, and running checks.

[Read the setup guide](https://hightierroach.github.io/delegateH/)

## Install

You need Codex with `gpt-6.1-sol`, Python 3.9+, Git, and the [Antigravity CLI](https://antigravity.google/docs/cli/getting-started/). Sign in to Antigravity with a personal Google AI Pro account that has Hydrogen access.

```sh
git clone https://github.com/HighTierRoach/delegateH.git
cd delegateH
mkdir -p "$HOME/.agents/skills"
test ! -e "$HOME/.agents/skills/delegateH" &&
  cp -R delegateH "$HOME/.agents/skills/"
python3 "$HOME/.agents/skills/delegateH/scripts/orchestrator.py" healthcheck
```

Use a fresh install destination. If the skill is already installed, review your local changes before updating it. Start a Codex session with GPT-6.1 Sol selected and enter:

```text
$delegateH AUTO review this change and delegate independent checks if useful.
```

The default worker is `gemini-4-hydrogen-medium`. The runner uses Antigravity account sign-in and included quota, with AI credit overages disabled. It excludes Gemini API keys and Cloud ADC environment settings. If the exact model is absent from your account catalog, the runner stops before dispatch. Use `healthcheck --probe` for a minimal live check after the model is listed.

Use `healthcheck --acp` to inspect the official Antigravity ACP session catalog and its session capabilities without submitting a prompt.

Local tests cover three concurrent fixture workers, separate Git snapshots, patch review and integration, failure handling, and cleanup. Live Hydrogen inference and concurrency have yet to be verified. macOS is the tested platform.

See the [operations guide](delegateH/references/operations.md) for manifest fields, scope rules, and patch review.

```sh
python3 -B -m unittest discover -s delegateH/tests -v
```
