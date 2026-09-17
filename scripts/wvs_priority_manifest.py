"""Generate the saved-catalog manifest for the next bounded WVS API phase."""
from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

CATALOG = Path("slop/research/wvs/20260917_openrouter_models.json")
MAP = Path("docs/wvs/wvs_map_data.json")
LEDGER = Path("slop/research/wvs/20260916_openrouter/wvs_iw_requests.jsonl")
OUT = Path("slop/research/wvs/20260917_priority_phase_manifest.md")
CALLS_PER_MODEL = 12 * 12
PHASE_STOP_USD = Decimal("35")
GLOBAL_STOP_USD = Decimal("80")

FAMILY_PREFIX = {
    "claude": "anthropic/", "deepseek": "deepseek/", "gemini": "google/",
    "gemma": "google/", "glm": "z-ai/", "gpt": "openai/", "grok": "x-ai/",
    "inkling": "thinkingmachines/", "kimi": "moonshotai/", "llama": "meta-llama/",
    "mistral": "mistralai/", "muse": "meta/", "qwen": "qwen/",
}


def displayed_id(model: dict[str, object]) -> str:
    return FAMILY_PREFIX[model["family"]] + model["name"]


def date(model: dict[str, object]) -> str:
    return datetime.fromtimestamp(model["created"], UTC).date().isoformat()


def price_per_million(model: dict[str, object], key: str) -> Decimal:
    return Decimal(model["pricing"][key]) * 1_000_000


def supports_structured(model: dict[str, object]) -> bool:
    return "structured_outputs" in model["supported_parameters"]


def row(model: dict[str, object], rationale: str) -> str:
    completion_bound = price_per_million(model, "completion") * Decimal(CALLS_PER_MODEL * 1024) / 1_000_000
    return (
        f"| `{model['id']}` | {date(model)} | {price_per_million(model, 'prompt'):g} | "
        f"{price_per_million(model, 'completion'):g} | {'yes' if supports_structured(model) else 'no'} | "
        f"USD {completion_bound:.4f} | {rationale} |"
    )


def ledger_cost() -> Decimal:
    cost = Decimal()
    for line in LEDGER.read_text().splitlines():
        event = json.loads(line)
        if event["event"] == "request_completed":
            cost += Decimal(str(event["usage"]["cost"]))
    return cost


def main() -> None:
    catalog = {model["id"]: model for model in json.loads(CATALOG.read_text())["data"]}
    plotted = {displayed_id(model) for model in json.loads(MAP.read_text())["models"]}

    def eligible(model: dict[str, object]) -> bool:
        return (
            not model["id"].endswith((":batch", ":free"))
            and supports_structured(model)
            and price_per_million(model, "completion") <= Decimal("15")
        )

    openai = [
        model for model in catalog.values()
        if model["id"].startswith("openai/")
        and eligible(model)
        and model["id"] not in plotted
        and "-pro" not in model["id"]
        and "fast" not in model["id"]
        and not any(word in model["id"] for word in ("codex", "image", "audio", "safeguard"))
        and model["id"] != "openai/gpt-chat-latest"
        and model["id"] not in {"openai/gpt-4o-2024-05-13", "openai/gpt-4o-mini-2024-07-18"}
    ]
    google = [
        model for model in catalog.values()
        if model["id"].startswith("google/gemini")
        and eligible(model)
        and model["id"] not in plotted
        and "-pro" not in model["id"]
        and "fast" not in model["id"]
        and not any(word in model["id"] for word in ("image", "customtools"))
    ]
    explicit = [
        "x-ai/grok-4.6", "x-ai/grok-4.5", "google/gemma-4-26b-a4b-it",
        "meta/muse-spark-1.2", "meta/muse-spark-1.1",
    ]
    selected_ids = [model["id"] for model in openai + google] + explicit
    selected = [catalog[model_id] for model_id in dict.fromkeys(selected_ids)]
    if set(selected_ids) & plotted:
        raise ValueError("priority manifest includes a plotted ID")
    if not all(eligible(model) for model in selected):
        raise ValueError("priority manifest includes an ineligible catalog entry")

    deferred_ids = [
        "qwen/qwen3.8-max-0902", "qwen/qwen3.8-2.4t-a95b", "z-ai/glm-5.3-flash",
        "mistralai/mistral-medium-3-5", "mistralai/mistral-small-2603",
        "mistralai/ministral-14b-2512", "mistralai/ministral-8b-2512",
        "mistralai/ministral-3b-2512",
    ]
    deferred = [catalog[model_id] for model_id in deferred_ids]
    total_completion_bound = sum(
        price_per_million(model, "completion") * Decimal(CALLS_PER_MODEL * 1024) / 1_000_000
        for model in selected
    )
    spend = ledger_cost()

    lines = [
        "# WVS priority API phase manifest, 2026-09-17",
        "",
        "This exact manifest is generated from the saved 444-record OpenRouter catalog snapshot, not a fresh paid request. It authorizes no calls by itself.",
        "",
        "## Guards",
        "",
        f"- A complete panel is {CALLS_PER_MODEL} initial calls, 12 items x 12 samples.",
        f"- Existing ledger spend is USD {spend:.10f}; the global stop remains USD {GLOBAL_STOP_USD}.",
        f"- This priority phase stops before USD {PHASE_STOP_USD} of new observed provider cost, even if the manifest has remaining models.",
        f"- Sum of 1024-token completion-only ceilings for all listed priority panels is USD {total_completion_bound:.4f}. This excludes prompt tokens and rescues, so it is not a spend authorization or a cost prediction.",
        "- Before every model, read cumulative `usage.cost` from the append-only ledger. Do not start a request whose conservative remaining cost could pass the phase or global stop.",
        "- A panel is publishable only as one exact protocol/run with 144 distinct item/sample keys. Never merge the two old incomplete Grok 4.5 attempts.",
        "",
        "## Required first diagnostic",
        "",
        "Run only this panel before any other manifest model. Audit repeats, parser outcomes, rescues, refusals, cache replay and provider cost before dispatching the priority batch.",
        "",
        "| exact ID | created UTC | input USD/M | output USD/M | structured | completion-only 144x1024 ceiling | rationale |",
        "|---|---:|---:|---:|---|---:|---|",
        row(catalog["openai/gpt-5-nano"], "required cheapest new 144-call diagnostic"),
        "",
        "## Priority manifest after diagnostic pass",
        "",
        "The order is Grok, OpenAI, Google, then the requested Muse points. `Flash` entries are retained because the user excluded `Fast`, not `Flash`.",
        "",
        "| exact ID | created UTC | input USD/M | output USD/M | structured | completion-only 144x1024 ceiling | rationale |",
        "|---|---:|---:|---:|---|---:|---|",
    ]
    diagnostic = catalog["openai/gpt-5-nano"]
    if diagnostic not in openai:
        raise ValueError("the required diagnostic is not eligible")
    groups = [
        ("Grok", [catalog["x-ai/grok-4.6"], catalog["x-ai/grok-4.5"]]),
        ("OpenAI", [model for model in sorted(openai, key=lambda model: (-model["created"], model["id"])) if model["id"] != diagnostic["id"]]),
        ("Google", sorted(google + [catalog["google/gemma-4-26b-a4b-it"]], key=lambda model: (-model["created"], model["id"]))),
        ("Muse", [catalog["meta/muse-spark-1.2"], catalog["meta/muse-spark-1.1"]]),
    ]
    for name, models in groups:
        lines.append(f"| **{name}** | | | | | | |")
        for model in models:
            rationale = "clean new full attempt" if model["id"] == "x-ai/grok-4.5" else "new direct panel"
            lines.append(row(model, rationale))

    lines.extend([
        "",
        "## Deferred approved shortlist",
        "",
        "These remain eligible only after the priority phase has a passing diagnostic and remaining observed budget. They are not queued by this manifest.",
        "",
        "| exact ID | created UTC | input USD/M | output USD/M | structured | completion-only 144x1024 ceiling | rationale |",
        "|---|---:|---:|---:|---|---:|---|",
    ])
    for model in deferred:
        lines.append(row(model, "deferred Qwen/GLM/Mistral shortlist"))
    lines.extend([
        "",
        "## Exclusions checked",
        "",
        "- Already complete/plotted direct IDs, including Grok 4.3 and 4.20, are excluded.",
        "- `:batch` and `:free` routes, `Pro` and `Fast` IDs, output prices above USD 15/M, and code/image/audio/safeguard/multi-agent variants are excluded.",
        "- `x-ai/grok-4.4` remains absent from the saved catalog.",
        "- `qwen/qwen3.5-flash-02-23` and the prior Grok 4.5 records are retained as incomplete evidence, not plotted or merged.",
        "",
        "-- PI[gpt-5.6-terra]",
    ])
    OUT.write_text("\n".join(lines) + "\n")
    print(f"wrote {OUT}: {len(selected)} priority models, {len(deferred)} deferred models, {CALLS_PER_MODEL * len(selected)} expected initial calls")


if __name__ == "__main__":
    main()
