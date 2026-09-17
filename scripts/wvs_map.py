"""WVS Inglehart-Welzel culture map with LABELED axes: place LLMs among human societies (the
Economist chart), on the two named IW dimensions instead of a blind PCA.

  X = Survival <-> Self-expression        (homosexuality tolerance, interpersonal trust, political action)
  Y = Traditional <-> Secular-Rational    (religion importance + belief, abortion, child autonomy)

Each axis is a small hand-picked battery of GlobalOpinionQA WVS items (moralmaps.iw_axes), every item
oriented to its axis-positive pole by reading the option order. A country's coordinate is the mean
`positiveness` (0-1) over that axis's items from the human WVS choice frequencies. A model's
coordinate is the SAME items administered as a dense Likert readout (read_items_rated: rate every
option 1-5 as JSON, binary options order-permuted to cancel positional bias, N samples, normalized
mean rating -> distribution), reduced identically; open models can instead use the answer-token
logprob reader (read_items). Each model also carries a bootstrap 95% CI (over items + samples) drawn
as error bars, so mushy / uncertain placements read as uncertain rather than confident dots. NB the
model coordinate is a rating-derived pseudo-distribution while the human one is a real choice
frequency -- a documented proxy. This is an APPROXIMATE IW (3 themes/axis, not the canonical 5 --
national pride/authority/materialism are absent from GlobalOpinionQA), not a verbatim reproduction.

  uv run python scripts/wvs_map.py --local-model Qwen/Qwen3-0.6B \
      --api-models meta-llama/llama-3.1-8b-instruct openai/gpt-4o-mini
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import dotenv
import numpy as np
import torch
from loguru import logger

dotenv.load_dotenv()
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer

from moralmaps import maps
from moralmaps.zones import zones_for, zone_of, IW_MACRO
from moralmaps.instrument import Instrument, InstrItem
from moralmaps.read import read_items, resolve_answer_ids
from moralmaps.read_api import rated_protocol_identity, read_items_rated
from moralmaps.rated_cache import merge_completed
from moralmaps.iw_axes import AXIS_ITEMS, X_AXIS, Y_AXIS, SKIP, resolve_items, positiveness

# option labels are single digits 0..n-1 -- single-token (unlike '10' on the justifiable scale) and
# the format the answer-token reader is tuned for (a bare digit, not a letter the model ignores in
# favour of the option word).
DIGITS = "0123456789"

# OpenRouter model IDs checked against https://openrouter.ai/api/v1/models on 2026-09-16.
# Selecting a set is explicit because every uncached entry makes paid API calls.
# These existing plotted families predate the saved OpenRouter catalog. The choice is an explicit
# release-order decision, not numeric parsing: Grok 4.3 is the observed series endpoint in README.
LEGACY_LATEST = {
    "gemma": "gemma-4-31b-it",
    "grok": "grok-4.3",
    "llama": "llama-4-maverick",
    "mistral": "mistral-large-2512",
}

# These historical coordinates predate the local metadata file. Their dates remain traceable
# to exact IDs in the saved 2026-09-17 OpenRouter catalog, not inferred from version strings.
LEGACY_CATALOG_IDS = {
    "grok-4.20": "x-ai/grok-4.20",
    "grok-4.3": "x-ai/grok-4.3",
    "gpt-5.4": "openai/gpt-5.4",
    "gpt-5.5": "openai/gpt-5.5",
}
SAVED_CATALOG_PATH = Path("slop/research/wvs/20260917_openrouter_models.json")
CAPABILITY_MAPPING_PATH = Path("slop/research/wvs/20260917_artificialanalysis/wvs_hle_mapping.json")
RATED_PROTOCOL_DIAGNOSTICS = {"gpt-5-nano (rated)"}

API_MODEL_SETS = {
    "fable-astra": (
        "anthropic/claude-fable-5.1",
        "openai/gpt-6-astra",
    ),
    "recent": (
        "anthropic/claude-fable-5.1",
        "openai/gpt-6-astra",
        "meta/muse-spark-1.3",
        "moonshotai/kimi-k3",
        "thinkingmachines/inkling",
        "deepseek/deepseek-v4.1-flash",
        "z-ai/glm-5.3",
        "z-ai/glm-5.3-flash",
        "google/gemini-3.7-flash",
        "x-ai/grok-4.5",
        "openai/gpt-5.6-sol",
    ),
}


def load_wvs_all() -> list[dict]:
    """Every WVS question with its substantive options (DK/refusal/Missing/INAP dropped) and each
    zone-mapped country's distribution renormalized over those options."""
    ds = load_dataset("Anthropic/llm_global_opinions", split="train")
    out = []
    for r in ds:
        if r["source"] != "WVS" or not r["question"]:
            continue
        opts = ast.literal_eval(r["options"]) if isinstance(r["options"], str) else r["options"]
        keep = [i for i, o in enumerate(opts) if not SKIP.search(o)]
        if len(keep) < 2:
            continue
        sel = ast.literal_eval(re.search(r"\{.*\}", r["selections"], re.S).group(0))
        dist = {}
        for c, ps in sel.items():
            if not zone_of(c):
                continue
            v = np.array([ps[i] for i in keep], float)
            if v.sum() > 0:
                dist[c] = v / v.sum()
        out.append({"q": r["question"], "opts": [opts[i] for i in keep], "dist": dist})
    return out


def human_axis_scores(resolved: dict[str, list[dict]]) -> tuple[list[str], np.ndarray]:
    """Per-country (X, Y). A country is kept if it covers at least half of each axis's items; its
    axis value is the mean positiveness over the items it does cover."""
    countries = sorted({c for items in resolved.values() for it in items for c in it["rec"]["dist"]})
    rows, keep = [], []
    for c in countries:
        xy, ok = [], True
        for axis in (X_AXIS, Y_AXIS):
            vals = [positiveness(it["rec"]["dist"][c], it["pole_idx"], it["n"])
                    for it in resolved[axis] if c in it["rec"]["dist"]]
            if len(vals) < (len(resolved[axis]) + 1) // 2:
                ok = False
                break
            xy.append(float(np.mean(vals)))
        if ok:
            keep.append(c)
            rows.append(xy)
    return keep, np.array(rows)


def build_instruments(resolved: dict[str, list[dict]]) -> tuple[list[Instrument], dict[str, dict]]:
    """One nominal Instrument per distinct option-count (answer_space = single letters), covering the
    union of both axes' items. Returns the instruments + a {suffix: {pole_idx, n, axis}} index."""
    items_by_n: dict[int, list[InstrItem]] = {}
    meta: dict[str, dict] = {}
    seen: set[str] = set()
    for axis, items in resolved.items():
        for it in items:
            s = it["suffix"]
            meta[s] = {"pole_idx": it["pole_idx"], "n": it["n"], "axis": axis}
            if s in seen:
                continue
            seen.add(s)
            n, opts = it["n"], it["rec"]["opts"]
            legend = "; ".join(f"{DIGITS[k]}) {o}" for k, o in enumerate(opts))
            task = f"Answer options: {legend}. Respond with only the number."
            items_by_n.setdefault(n, []).append(
                InstrItem(id=s, prompt=it["rec"]["q"], dimension="iw", sign=1,
                          frame="forward", meta={"task": task}))
    instrs = [Instrument(name=f"wvs_iw_n{n}", construct="opinion", kind="nominal",
                         answer_space=list(DIGITS[:n]), dimensions=["iw"], items=its,
                         prefill="(", display="WVS-IW")
              for n, its in sorted(items_by_n.items())]
    return instrs, meta


def model_axis_scores(vecs: dict[str, np.ndarray], meta: dict[str, dict],
                      resolved: dict[str, list[dict]]) -> tuple[float, float]:
    """(X, Y) for one model from its per-item p vectors (suffix -> p over options)."""
    xy = []
    for axis in (X_AXIS, Y_AXIS):
        vals = [positiveness(vecs[it["suffix"]], it["pole_idx"], it["n"]) for it in resolved[axis]]
        xy.append(float(np.mean(vals)))
    return xy[0], xy[1]


def read_model(rows: list[dict], meta: dict[str, dict]) -> dict[str, np.ndarray]:
    """rows from read_items -> {suffix: p over that item's options}. NaN p (read collapse) fails loud
    later via positiveness rather than being imputed."""
    return {r["id"]: np.asarray(r["p"], float)[: meta[r["id"]]["n"]] for r in rows}


def _sample_only_coord_se(psamples: dict[str, np.ndarray], resolved: dict[str, list[dict]],
                          rng: np.random.Generator, n_draws: int, B: int = 500) -> tuple[float, float]:
    """Response-mean bootstrap SE with the WVS item set held fixed."""
    samples = []
    for _ in range(B):
        xy = []
        for axis in (X_AXIS, Y_AXIS):
            vals = []
            for it in resolved[axis]:
                ps = psamples[it["suffix"]]
                mean_p = ps[rng.integers(0, len(ps), n_draws)].mean(0)
                vals.append(positiveness(mean_p, it["pole_idx"], it["n"]))
            xy.append(float(np.mean(vals)))
        samples.append(xy)
    return tuple(np.std(samples, axis=0))


def model_coord_ci(psamples: dict[str, np.ndarray], resolved: dict[str, list[dict]],
                   rng: np.random.Generator, B: int = 500) -> tuple[float, float, float, float]:
    """(x, y, x_se, y_se), combined item-and-response-mean bootstrap uncertainty.

    The point uses each item's mean over its N ratings. Each replicate resamples items and, for every
    selected item, resamples N ratings then averages them. This estimates uncertainty of the N-sample
    mean rather than uncertainty of a single response. The separate `_sample_only_coord_se` keeps the
    fixed-item response component available for diagnostics.
    """
    def axis_coords(getp) -> list[float]:
        return [float(np.mean([positiveness(getp(it), it["pole_idx"], it["n"]) for it in resolved[axis]]))
                for axis in (X_AXIS, Y_AXIS)]
    x, y = axis_coords(lambda it: psamples[it["suffix"]].mean(0))
    bx, by = [], []
    for _ in range(B):
        xy = []
        for axis in (X_AXIS, Y_AXIS):
            items = resolved[axis]
            vals = []
            for j in rng.integers(0, len(items), len(items)):
                it = items[j]
                ps = psamples[it["suffix"]]
                mean_p = ps[rng.integers(0, len(ps), len(ps))].mean(0)
                vals.append(positiveness(mean_p, it["pole_idx"], it["n"]))
            xy.append(float(np.mean(vals)))
        bx.append(xy[0]); by.append(xy[1])
    return x, y, float(np.std(bx)), float(np.std(by))


def ci_bootstrap_smoke() -> None:
    """Sample-only SE must shrink by roughly sqrt(N) when ratings are averaged."""
    resolved = {axis: [{"suffix": f"{axis}{i}", "pole_idx": 1, "n": 2} for i in range(3)]
                for axis in (X_AXIS, Y_AXIS)}
    psamples = {item["suffix"]: np.tile([[1.0, 0.0], [0.0, 1.0]], (128, 1))
                for items in resolved.values() for item in items}
    se_one = _sample_only_coord_se(psamples, resolved, np.random.default_rng(0), n_draws=1, B=10_000)
    se_sixteen = _sample_only_coord_se(psamples, resolved, np.random.default_rng(1), n_draws=16, B=10_000)
    ratio = float(np.mean(se_one) / np.mean(se_sixteen))
    assert 3.5 < ratio < 4.5, f"sample-only SE ratio {ratio:.3f}, expected sqrt(16)=4"
    print(f"ci smoke: sample-only SE ratio N=1/N=16 is {ratio:.3f}, expected 4.000")


def cluster_outlier_sd(countries: list[str], P: np.ndarray, models: dict[str, tuple],
                       min_n: int = 8) -> list[tuple]:
    """How odd each model looks as a member of each human macro-zone, in cluster SDs.

    Two readings per (model, zone). The signed per-axis z says which way and how far on one named
    axis, so `+2.9` on secular-rational reads as "2.9 sigma more secular-rational than the average
    member of this zone". The Mahalanobis distance says how odd the placement is overall, using the
    zone's own 2x2 covariance; it is the honest scalar because the zones are elongated and tilted
    (the West runs diagonally), so a model far along a zone's own long axis is less of an outlier
    than a plain z suggests. Zones under min_n countries are skipped: a 2x2 covariance from a handful
    of points is mostly noise."""
    by_zone: dict[str, list[int]] = {}
    for i, c in enumerate(countries):
        z = zone_of(c)
        if z is not None:
            by_zone.setdefault(IW_MACRO[z], []).append(i)
    out = []
    for zone, idx in sorted(by_zone.items()):
        if len(idx) < min_n:
            continue
        Z = P[idx]
        mu, sd = Z.mean(0), Z.std(0, ddof=1)
        # ridge keeps the inverse finite if a zone is near-degenerate on one axis
        S = np.cov(Z.T) + 1e-6 * np.eye(2)
        Sinv = np.linalg.inv(S)
        for name, v in models.items():
            d = np.array([v[0], v[1]]) - mu
            out.append((name.replace(" (rated)", ""), zone, len(idx),
                        float(d[0] / sd[0]), float(d[1] / sd[1]),
                        float(np.sqrt(d @ Sinv @ d))))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--local-model", default="",
                    help="optional local checkpoint, blank preserves the API-only published map")
    ap.add_argument("--api-models", nargs="*", default=[])
    ap.add_argument("--api-model-set", choices=API_MODEL_SETS,
                    help="explicit paid OpenRouter model set, combined with --api-models")
    ap.add_argument("--api-samples", type=int, default=12,
                    help="rating samples per item (each dense: every option rated), binary items order-balanced")
    ap.add_argument("--api-concurrency", type=int, default=8,
                    help="maximum concurrent OpenRouter calls, reduced for a provider that reports rate limits")
    ap.add_argument("--api-request-timeout", type=float, default=90.0)
    ap.add_argument("--api-max-tokens", type=int, default=1024,
                    help="output budget per rating call; large enough that a reasoning model finishes the JSON")
    ap.add_argument("--ci-smoke", action="store_true",
                    help="check that response-mean bootstrap SE falls approximately as 1/sqrt(N)")
    reasoning_group = ap.add_mutually_exclusive_group()
    reasoning_group.add_argument("--api-disable-reasoning", action="store_true",
                                 help="send reasoning.enabled=false for models whose catalog metadata says optional")
    reasoning_group.add_argument("--api-reasoning-effort",
                                 help="send a mandatory model's catalog-supported minimum reasoning effort")
    ap.add_argument("--api-structured-output", action="store_true",
                    help="request a strict score-all-options JSON schema only for a catalog-confirmed supporting model")
    ap.add_argument("--api-provider-json",
                    help="OpenRouter provider policy JSON, included in the score-all-options protocol identity")
    ap.add_argument("--api-require-complete", action="store_true",
                    help="exit nonzero rather than render after an explicitly requested API panel is incomplete")
    ap.add_argument("--api-probe-first", action="store_true",
                    help="send sample 0 first and abort before the other 143 calls if it is not parse-valid")
    ap.add_argument("--max-think-tokens", type=int, default=64)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--out", default="docs/img/wvs/wvs_map_iw.png")
    ap.add_argument("--web-data", type=Path,
                    help="write the coordinates, zones, family colors, and labels shared by the SVG page")
    ap.add_argument("--cache", default="slop/research/wvs/20260916_openrouter/wvs_iw_rated.json",
                    help="durable completed-panel cache, tracked with the request evidence")
    ap.add_argument("--records", default="slop/research/wvs/20260916_openrouter/wvs_iw_requests.jsonl",
                    help="fsynced JSONL request ledger, outside /tmp and retained for reuse")
    ap.add_argument("--include-all-cached", action="store_true",
                    help="render every complete durable cache entry without making an API request")
    args = ap.parse_args()
    if args.ci_smoke:
        ci_bootstrap_smoke()
        return
    api_models = list(dict.fromkeys(args.api_models + list(API_MODEL_SETS.get(args.api_model_set, ()))))
    api_reasoning = ({"enabled": False} if args.api_disable_reasoning else
                     {"effort": args.api_reasoning_effort} if args.api_reasoning_effort else None)
    api_provider = json.loads(args.api_provider_json) if args.api_provider_json else None

    recs = load_wvs_all()
    resolved = resolve_items(recs)
    for axis, items in resolved.items():
        logger.info(f"{axis}: " + ", ".join(f"{it['suffix']}[n{it['n']},pole{it['pole_idx']}]"
                                             for it in items))
    countries, P = human_axis_scores(resolved)
    logger.info(f"{len(recs)} WVS questions -> {len(countries)} countries on 2 IW axes")

    # One rated item per distinct WVS question (canonical option order), administered to every API model.
    rated_items, seen = [], set()
    for axis in (X_AXIS, Y_AXIS):
        for it in resolved[axis]:
            if it["suffix"] in seen:
                continue
            seen.add(it["suffix"])
            rated_items.append({"id": it["suffix"], "question": it["rec"]["q"],
                                "options": it["rec"]["opts"], "n": it["n"]})

    cpath = Path(args.cache)
    cpath.parent.mkdir(parents=True, exist_ok=True)
    cache = json.loads(cpath.read_text()) if cpath.exists() else {"schema": 2, "completed": {}}
    if cache["schema"] != 2:
        raise ValueError(f"unsupported WVS cache schema {cache['schema']}")

    def published_models(path: Path) -> dict[str, tuple]:
        """Reuse the committed historical coordinates, which are rounded display values, not raw reruns."""
        models = {}
        for line in path.read_text().splitlines():
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 5 or cells[0] in ("model", "") or set(cells[1]) <= set(":- "):
                continue
            x, y, x_ci95, y_ci95 = (float(cell) for cell in cells[1:5])
            models[cells[0]] = (x, y, x_ci95 / 1.96, y_ci95 / 1.96)
        return models

    published_ci = Path("docs/img/wvs/wvs_model_ci.md")
    models: dict[str, tuple] = published_models(published_ci) if published_ci.exists() else {}
    if args.include_all_cached:
        for entry in cache["completed"].values():
            if entry["display_key"] not in RATED_PROTOCOL_DIAGNOSTICS:
                models[entry["display_key"]] = tuple(entry["coords"])

    def save_cache() -> None:
        """Merge completed panels under a lock so parallel lanes cannot erase one another."""
        nonlocal cache
        cache = merge_completed(cpath, cache["completed"])

    rng = np.random.default_rng(0)                       # deterministic bootstrap

    # Open local model: answer-token logprob reader (single-choice categorical) -> (x, y), no CI.
    if args.local_model:
        key = args.local_model.split("/")[-1] + " (lp)"
        if key not in models:
            instrs, meta = build_instruments(resolved)
            tok = AutoTokenizer.from_pretrained(args.local_model)
            if tok.pad_token is None:
                tok.pad_token = tok.eos_token
            tok.padding_side = "left"
            lm = AutoModelForCausalLM.from_pretrained(args.local_model, dtype=torch.bfloat16).to(args.device).eval()
            rows = []
            for k, instr in enumerate(instrs):
                rows += read_items(lm, tok, instr, instr.items,
                                   resolve_answer_ids(tok, instr.answer_space),
                                   max_think_tokens=args.max_think_tokens, batch_size=16,
                                   verbose_first=(k == 0))
            models[key] = model_axis_scores(read_model(rows, meta), meta, resolved)
            save_cache()

    # API models: score-all-options readout -> (x, y, x_se, y_se) with bootstrap CI.
    for m in api_models:
        key = m.split("/")[-1] + " (rated)"
        protocol_id = rated_protocol_identity(
            m, rated_items, n_samples=args.api_samples, temperature=1.0,
            max_tokens=args.api_max_tokens, concurrency=args.api_concurrency,
            req_timeout=args.api_request_timeout, reasoning=api_reasoning,
            structured_output=args.api_structured_output, provider=api_provider)
        completed = cache["completed"].get(protocol_id)
        if completed is not None:
            models[key] = tuple(completed["coords"])
            logger.info(f"cache hit {key}: protocol={protocol_id[:12]}")
            continue
        rows = read_items_rated(m, rated_items, n_samples=args.api_samples,
                                max_tokens=args.api_max_tokens, concurrency=args.api_concurrency,
                                req_timeout=args.api_request_timeout, reasoning=api_reasoning,
                                structured_output=args.api_structured_output,
                                records_path=args.records, verbose_first=True, provider=api_provider,
                                probe_first=args.api_probe_first)
        incomplete = [row["id"] for row in rows if row["valid_samples"] != args.api_samples]
        if incomplete:
            message = f"{key}: incomplete items {incomplete}; raw evidence is in {args.records}; not cached or plotted"
            logger.warning(message)
            if args.api_require_complete:
                raise RuntimeError(message)
            continue
        psamples = {row["id"]: np.array(row["p_samples"]) for row in rows}
        models[key] = model_coord_ci(psamples, resolved, rng)
        cache["completed"][protocol_id] = {
            "model": m,
            "display_key": key,
            "coords": list(models[key]),
            "records_path": args.records,
            "run_id": rows[0]["run_id"],
            "protocol_id": protocol_id,
            "n_items": len(rows),
            "n_samples": args.api_samples,
            "ci_method": "combined item and N-response-mean bootstrap",
        }
        save_cache()
        x, y, xs, ys = models[key]
        logger.info(f"cached {key}: ({x:.2f}, {y:.2f}) +-({1.96*xs:.02f}, {1.96*ys:.02f}) 95% CI")

    # Uncertainty as a TABLE, not whiskers on the map (the CI crosses overlap into noise with a dozen+
    # models). Sorted widest-first so the mushy models are obvious. The CI is bootstrap over items +
    # samples; for the wide ones it's item-disagreement (the model rates different WVS items
    # inconsistently on an axis), which more samples will NOT shrink -- see the readme/journal note.
    ci_rows = [(k, v[0], v[1], 1.96 * v[2], 1.96 * v[3]) for k, v in models.items() if len(v) > 3]
    if ci_rows:
        from tabulate import tabulate
        ci_rows.sort(key=lambda r: -(r[3] + r[4]))
        table = tabulate(ci_rows, headers=["model", "x self-expr", "y secular", "x 95%CI", "y 95%CI"],
                         tablefmt="pipe", floatfmt="+.2f")
        Path(args.out).with_name("wvs_model_ci.md").write_text(table + "\n")
        logger.info("model coords + 95% CI (widest first):\n" + table)

    # scripts/wvs_outlier_table.py turns wvs_model_ci.md into the zone-SD outlier table. It reads the
    # committed coords rather than the cache, so it reruns offline without paying for 17 models again.

    # Render through the SHARED value-map renderer (same one the instrument value maps use): pole
    # signposts through the human median, 4 auto-selected zone hulls, auto-placed labels, model stars.
    _, emph = zones_for(countries)
    # The hero map (unlike the instrument maps) bakes on a title + an attribution note carrying the
    # repo URL, so copies shared around the web stay credited and self-explanatory. Everything else
    # still leans on the README voice.
    # Drop the " (rated)" readout tag from the on-map labels (the cache/CI-table keep it) -- the map is
    # crowded and every model here is rated, so the tag adds nothing.
    plot_models = {k.replace(" (rated)", ""): v for k, v in models.items()}
    # Too many model names to label them all. Plot every star (colour = family) but label only the
    # latest catalogued release in each family. Numeric version strings do not establish release order.
    fams: dict[str, list[str]] = {}
    for k in plot_models:
        family = maps.model_family(k)
        if family is None:
            raise ValueError(f"model has no explicit family: {k}")
        fams.setdefault(family, []).append(k)
    metadata = json.loads(Path("docs/img/wvs/wvs_model_metadata.json").read_text())["models"]
    saved_catalog = {entry["id"]: entry for entry in json.loads(SAVED_CATALOG_PATH.read_text())["data"]}
    legacy_release_dates = {
        name: datetime.fromtimestamp(saved_catalog[model_id]["created"], tz=timezone.utc).date().isoformat()
        for name, model_id in LEGACY_CATALOG_IDS.items()
    }
    completed_by_name = {entry["display_key"].replace(" (rated)", ""): entry
                         for entry in cache["completed"].values()}

    def release_created(name: str) -> str | None:
        if name in metadata:
            return metadata[name]["created"]
        panel = completed_by_name.get(name)
        if panel is not None and panel["model"] in saved_catalog:
            return datetime.fromtimestamp(saved_catalog[panel["model"]]["created"], tz=timezone.utc).date().isoformat()
        return legacy_release_dates.get(name)

    model_labels: dict[str, str] = {}
    label_sources: dict[str, str] = {}
    for family, names in fams.items():
        dated = [name for name in names if release_created(name) is not None]
        if dated:
            latest = max(dated, key=release_created)
            label_sources[family] = f"catalog created={release_created(latest)}"
        else:
            latest = LEGACY_LATEST[family]
            if latest not in names:
                raise ValueError(f"legacy latest {latest} absent from plotted {family} family")
            label_sources[family] = "explicit legacy release-order choice"
        model_labels[latest] = latest.replace("claude-", "")
    if args.web_data:
        # This artifact is the shared geometry contract for the static, vanilla SVG and React maps.
        # It stores the already-oriented coordinates and the static renderer's annotation policy.
        from shapely.geometry import MultiPoint

        zones_all, _ = zones_for(countries)
        sx, sy = maps.orient_geographic(P, countries, zones_all)
        Pplot = P * np.array([sx, sy])
        zones, dot_cols, label_set = maps._map_annotations(Pplot, countries, zones_all, emph, "#888888")
        cidx = {country: i for i, country in enumerate(countries)}
        buf = 0.022 * float(np.hypot(*(Pplot.max(0) - Pplot.min(0))))
        zone_hulls = []
        for zone, members in zones.items():
            pts = [tuple(Pplot[cidx[country]]) for country in members if country in cidx]
            if len(pts) < 2:
                raise ValueError(f"zone {zone} lacks two plotted countries")
            coords = np.asarray(MultiPoint(pts).convex_hull.buffer(buf, quad_segs=16).exterior.coords)
            # The static renderer's region allocator starts from the whole hull perimeter. The
            # browser's expanding-ring allocator starts from the centroid, so its first viable
            # candidate remains adjacent to the corresponding coloured boundary.
            centroid = coords[:-1].mean(axis=0)
            zone_hulls.append({"name": zone, "color": maps.ZONE_COLORS[zone],
                               "points": coords.tolist(), "label_anchor": centroid.tolist()})

        completed = {entry["display_key"].replace(" (rated)", ""): entry
                     for entry in cache["completed"].values()}
        capability_source = json.loads(CAPABILITY_MAPPING_PATH.read_text())
        raw_capability_source = CAPABILITY_MAPPING_PATH.parent / capability_source["source"]["decoded_models"]
        raw_source_hash = hashlib.sha256(raw_capability_source.read_bytes()).hexdigest()
        if raw_source_hash != capability_source["source"]["decoded_models_sha256"]:
            raise ValueError(f"Artificial Analysis HLE source hash mismatch: {raw_capability_source}")
        capability_by_model = {entry["plotted_model"]: entry for entry in capability_source["mappings"]}
        if len(capability_by_model) != len(capability_source["mappings"]):
            raise ValueError("Artificial Analysis mapping repeats a plotted model")
        unknown_capability_models = set(capability_by_model) - set(plot_models)
        if unknown_capability_models:
            raise ValueError(f"Artificial Analysis mapping names absent plotted models: {sorted(unknown_capability_models)}")
        family_logos = {
            "claude": "logos/anthropic.svg", "deepseek": "logos/deepseek.svg",
            "gemini": "logos/google.svg", "gemma": "logos/google.svg",
            "glm": "logos/z-ai.svg", "gpt": "logos/openai.svg", "grok": "logos/x-ai.svg",
            "inkling": "logos/thinkingmachines.svg", "kimi": "logos/moonshotai.svg",
            "llama": "logos/meta.svg", "mistral": "logos/mistral.svg", "muse": "logos/meta.svg",
            "qwen": "logos/qwen.svg",
        }

        def model_provenance(name: str) -> dict[str, object]:
            panel = completed.get(name)
            catalog = metadata.get(name)
            if catalog is None and panel is not None and panel["model"] in saved_catalog:
                catalog = {"created": datetime.fromtimestamp(
                    saved_catalog[panel["model"]]["created"], tz=timezone.utc).date().isoformat()}
            if panel is None:
                legacy_date = legacy_release_dates.get(name)
                provenance = {"readout": "recovered rounded historical coordinate", "items": None,
                              "samples": None, "run_id": None, "protocol_id": None,
                              "release_created": legacy_date,
                              "release_source": (f"saved OpenRouter catalog 2026-09-17: {LEGACY_CATALOG_IDS[name]}"
                                                 if legacy_date else "historical coordinate")}
            else:
                provenance = {"readout": "rated categorical response", "items": panel["n_items"],
                              "samples": panel["n_samples"], "run_id": panel["run_id"],
                              "protocol_id": panel["protocol_id"],
                              "release_created": catalog["created"] if catalog else None,
                              "release_source": "catalog" if catalog else "request ledger"}
            capability = capability_by_model.get(name)
            provenance["hle_score"] = capability["hle_score"] if capability else None
            provenance["hle_source_name"] = capability["source_name"] if capability else None
            provenance["hle_source_effort"] = capability["source_effort"] if capability else None
            return provenance

        args.web_data.parent.mkdir(parents=True, exist_ok=True)
        args.web_data.write_text(json.dumps({
            "schema": 3,
            "capability_x": {
                "label": "HLE score",
                "source_url": capability_source["source"]["hle_url"],
                "fetched_utc": capability_source["source"]["fetched_utc"],
                "raw_source": str(raw_capability_source),
                "raw_source_sha256": raw_source_hash,
                "mapping": str(CAPABILITY_MAPPING_PATH),
                "selection_rule": capability_source["selection_rule"],
                "matched_models": len(capability_by_model),
                "status": "available",
                "metric": capability_source["source"]["metric"],
                "protocol": capability_source["source"]["protocol"],
            },
            "title": "Moral Maps: Where Do Frontier\nModels' Cultural Values Lie?",
            "note": "source: github.com/wassname/moral-maps",
            "axis": {"x": (["Self-expression", "Survival"] if sx < 0 else ["Survival", "Self-expression"]),
                     "y": (["Secular-Rational", "Traditional"] if sy < 0 else ["Traditional", "Secular-Rational"])},
            "median": {"x": float(np.median(Pplot[:, 0])), "y": float(np.median(Pplot[:, 1]))},
            "countries": [{"name": name, "x": float(x), "y": float(y), "color": color,
                           "label": name if name in label_set else None}
                          for name, (x, y), color in zip(countries, Pplot, dot_cols)],
            "zones": zones,
            "zone_hulls": zone_hulls,
            "logos": family_logos,
            "latest_by_family": {family: {"name": name, "source": label_sources[family]}
                                 for family, names in fams.items() for name in names if name in model_labels},
            "models": [{"name": name, "x": float(v[0] * sx), "y": float(v[1] * sy),
                        "family": maps.model_family(name), "color": maps.model_family_color(name),
                        "label": model_labels.get(name), "provenance": model_provenance(name)}
                       for name, v in plot_models.items()],
        }, indent=2, sort_keys=True) + "\n")
    # Poles in NATURAL data order (x_neg, x_pos, y_neg, y_pos): raw X is high on Self-expression, raw Y
    # high on Secular-Rational. plot_value_map's orient_geographic then flips X so the cultural West
    # lands in the west (Self-expression left) and confirms African-Islamic sits south -- the same
    # orientation every other map now uses, so we build a better map than the Economist's, consistently.
    fig = maps.plot_value_map(
        "WVS Inglehart-Welzel", countries, P,
        ("Survival", "Self-expression", "Traditional", "Secular-Rational"),
        models=plot_models, model_labels=model_labels, emphasize=emph,
        title="Frontier LLMs on the\nWorld Values Survey",
        note=f"{len(plot_models)} models, rated sampling\ngithub.com/wassname/moral-maps")
    fig.savefig(args.out, dpi=200, bbox_inches="tight")
    fig.savefig(Path(args.out).with_suffix(".svg"), bbox_inches="tight")
    logger.info(f"wrote {args.out}")


if __name__ == "__main__":
    main()
