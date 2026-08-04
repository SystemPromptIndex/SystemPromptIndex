# Contributing

This repository is the public dataset behind
[systempromptindex.ai](https://systempromptindex.ai): the prompt corpus and
its AISPA audits. Contributions that add prompts, correct provenance, or
challenge an audit are all welcome.

## Adding a prompt

Open an issue or a pull request with:

- **The prompt text**, complete rather than excerpted.
- **Where it came from** — a link to the public source, and roughly when it was
  collected. A prompt with no traceable source cannot go in.
- **Which product and version** it belongs to.

Add it as `prompts/<vendor>/<product>.md`, matching the front matter of the
files already there. You do not need to supply an audit; the corpus and the
audits move independently.

## Correcting an audit

This is the most useful kind of contribution, and the bar is low: you do not
need to be right, you need to be specific.

Point at the span — the `text`, `start`, and `end` in the relevant
`audits/<vendor>/<product>.json` — and say what you would score it instead and
why. A disagreement about one instruction is worth more than a general
objection to the audit as a whole.

Two things worth knowing before you file one:

- **A span scored problematic that reads benign to you is the most useful
  report we get.** Over-flagging is the failure mode this corpus is most
  exposed to, and it is hard to find from the inside.
- **Some scores are contested by design.** Spans marked `"risky": true` sit on
  the line between user agency and platform safety. Those are documented
  disagreements rather than oversights — but arguing a specific one is still
  fair game.

## Fixing metadata

Wrong vendor, wrong product name, wrong version, a prompt filed under the wrong
company, a duplicate — all fine to send as a pull request. Keep `id` in sync
with the file path if you move a file.

## What does not belong here

- API keys, tokens, credentials, cookies, or private URLs.
- Prompts obtained by bypassing access controls. This index reproduces prompts
  that are already public; it is not a place to publish ones that are not.
- Personal data, private conversations, or user identifiers.
- Anything identifying who produced a given audit. This repository publishes
  findings; the procedure behind them is described in the
  [paper](https://arxiv.org/abs/2607.28617).

## Scope

This repository holds data. The website, the audit procedure, and the analysis
behind the paper are not here — the method is written up in the
[paper](https://arxiv.org/abs/2607.28617). Issues about the site itself are
still welcome; they will be routed.
