# Root React WVS image/a11y review

Reviewer: reviewer-openai, read-only, 2026-09-17.

## Verdict before follow-up

Changes requested.

1. `docs/index.html` had only a module script, stylesheet link, and root div. Add document language, title, and viewport metadata.
2. Both release panels used `release-tooltip` as their tooltip ID. Mixed keyboard/pointer use could create duplicate IDs and ambiguous descriptions. Use panel-specific tooltip IDs.

## Passed source/image checks

- Root source is React; `/wvs/` remains standalone static; `/wvs/react/` is a redirect and does not load a second bundle.
- The reader-facing introduction has no implementation archaeology, model count, or Artificial Analysis claim.
- Main map and both panel SVGs have title/description IDs referenced from `aria-labelledby`; descriptions derive visible counts and families from hidden-family state.
- Embedded logos are decorative and parent controls/markers carry names.
- Default and Qwen-hidden screenshots show country and region geometry unchanged while Qwen marks disappear.
- The supplied map tooltip is readable and contains model-specific fields.

Evidence limit: this reviewer inspected source and captures, not a browser accessibility tree or deployed output.

-- reviewer-openai
