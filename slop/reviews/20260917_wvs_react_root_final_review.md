# Final review: root React WVS deployment

Reviewer: `reviewer`, read-only, 2026-09-17.

## Verdict

PASS. The root document has `lang=en`, viewport metadata, and the WVS title. It loads the current root React bundle. The standalone `/wvs/` renderer remains, while `/wvs/react/` is a redirect stub with no second bundle.

## Observed

- Main map uses `role=img` with `aria-labelledby="map-svg-title map-svg-desc"`, one stable title and one visibility-dependent description.
- Both scatter panels have their own title/description pairs and per-panel tooltip IDs: `release-y-tooltip` and `release-x-tooltip`.
- Chip and marker logos are decorative. Parent controls and markers have accessible names.
- The root copy is reader-facing and has no visible Artificial Analysis claim, model-count wording, or implementation archaeology.
- Default, Qwen-hidden, tooltip, and side-by-side captures are legible. The Qwen state removes its marks and label while countries and zones do not move.
- `scripts/wvs_react/uat.py` records successful localhost checks for 64 models, 90 countries, median/model/country equality with shared JSON, SVG descriptions, tooltip/focus behavior, root route, static route, redirect compatibility, and Qwen visibility behavior.

## Limits

The review inspected source and captures, not the public deployment or a screen-reader session. Tooltip descriptions mount only when a mark is active, and focusable marks use `role=button` even though Enter/Space has no action. These are non-blocking for the assigned root/a11y revision.

-- reviewer
