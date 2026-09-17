"""Playwright UAT for the root React WVS page. No network calls leave localhost."""
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import date
import subprocess
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "slop/research/wvs/20260916_openrouter"
BASE = "http://localhost:8081"
VIEWPORT = {"width": 1440, "height": 1800}


def screenshot(page, url: str, name: str) -> Path:
    page.goto(url, wait_until="networkidle")
    page.screenshot(path=OUT / name, full_page=True)
    return OUT / name


def svg_description(page, selector: str, title_id: str, desc_id: str) -> None:
    svg = page.locator(selector)
    assert svg.get_attribute("role") == "img"
    assert svg.get_attribute("aria-labelledby") == f"{title_id} {desc_id}"
    assert svg.locator(f"title#{title_id}").count() == 1
    assert svg.locator(f"desc#{desc_id}").count() == 1
    assert svg.locator(f"desc#{desc_id}").text_content()


def country_positions(page) -> list[list[str]]:
    return page.locator("circle.country").evaluate_all(
        "nodes => nodes.map(node => [node.getAttribute('cx'), node.getAttribute('cy')])"
    )


def ols_slope(models: list[dict], value: str) -> float:
    dates = [date.fromisoformat(model["provenance"]["release_created"]).toordinal() for model in models]
    coordinates = [model[value] for model in models]
    date_mean = sum(dates) / len(dates)
    coordinate_mean = sum(coordinates) / len(coordinates)
    return sum((date - date_mean) * (coordinate - coordinate_mean) for date, coordinate in zip(dates, coordinates)) / sum((date - date_mean) ** 2 for date in dates)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    chrome = shutil.which("google-chrome")
    if chrome is None:
        raise RuntimeError("google-chrome is required for the Playwright UAT")
    data = json.loads((ROOT / "docs/wvs/wvs_map_data.json").read_text())
    assert data["schema"] == 3
    assert data["capability_x"]["status"] == "available"
    assert data["capability_x"]["source_url"] == "https://artificialanalysis.ai/evaluations/humanitys-last-exam"
    assert data["capability_x"]["fetched_utc"] == "2026-09-17T10:13:20Z"
    capability_matched = [model for model in data["models"] if model["provenance"]["hle_score"] is not None]
    assert len(capability_matched) == data["capability_x"]["matched_models"] == 46
    assert len(data["countries"]) == 90
    assert len(data["zone_hulls"]) == 4
    assert len(data["latest_by_family"]) == 13
    assert all(len(zone["points"]) >= 30 for zone in data["zone_hulls"])
    dated = [model for model in data["models"] if model["provenance"]["release_created"]]
    grok_dates = {model["name"]: model["provenance"]["release_created"] for model in data["models"] if model["name"] in {"grok-4.20", "grok-4.3"}}
    assert grok_dates == {"grok-4.20": "2026-03-31", "grok-4.3": "2026-04-30"}
    assert all(model["provenance"]["release_source"].startswith("saved OpenRouter catalog 2026-09-17: x-ai/")
               for model in data["models"] if model["name"] in grok_dates)
    families = {model["family"] for model in data["models"]}

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=chrome, headless=True, args=["--no-sandbox"])
        page = browser.new_page(viewport=VIEWPORT)
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))

        screenshot(page, f"{BASE}/img/wvs/wvs_map_iw.png", "wvs_static_playwright.png")
        screenshot(page, f"{BASE}/wvs/", "wvs_static_redirect.png")
        page.wait_for_selector("svg .model-mark")
        assert page.url == f"{BASE}/"

        screenshot(page, f"{BASE}/", "wvs_react_root_playwright_default.png")
        page.wait_for_selector("svg .model-mark")
        assert page.title() == "Moral Maps: Where Do Frontier Models' Cultural Values Lie?"
        assert page.locator("html").get_attribute("lang") == "en"
        assert page.locator('meta[name="viewport"]').count() == 1
        assert page.locator("h1").inner_text() == "Moral Maps: Where Do Frontier Models' Cultural Values Lie?"
        assert page.locator(".lede").inner_text() == "We start with the World Values Survey, a map of human values across about ninety countries."
        visible_copy = page.locator("main").inner_text()
        for absent in ("React/SVG rendering", "Historical coordinates", "Dated releases only"):
            assert absent not in visible_copy
        assert "Artificial Analysis HLE score" in visible_copy
        assert "redistribution permission" not in visible_copy
        capability_option = page.get_by_label("Release-panel x axis").locator('option[value="capability"]')
        assert capability_option.get_attribute("disabled") is None
        assert page.locator('.release-axis-selector a[href="https://artificialanalysis.ai/evaluations/humanitys-last-exam"]').count() == 1
        assert "saved 2026-09-17" in page.locator(".release-axis-selector").inner_text()
        layout_order = page.locator("main > *").evaluate_all("nodes => nodes.map(node => node.className.baseVal || node.className || node.tagName)")
        assert layout_order.index("chart-shell") < layout_order.index("map-explanation") < layout_order.index("release-panels") < layout_order.index("caption")
        assert page.locator(".release-panels .release-axis-selector").count() == 1
        assert "weak descriptive correlations" in page.locator(".caption").inner_text()
        assert "code and records" in page.locator(".caption").inner_text()

        map_svg = page.locator("svg[data-median-x]")
        svg_description(page, "svg[data-median-x]", "map-svg-title", "map-svg-desc")
        assert page.locator("path.zone").count() == 4
        assert page.locator("polygon.zone").count() == 0
        assert page.locator(".map-note").get_attribute("text-anchor") == "start"
        assert float(page.locator(".map-note").get_attribute("x")) == float(page.locator(".map-title").get_attribute("x"))
        assert float(page.locator(".map-note").get_attribute("y")) > float(page.locator(".map-title").get_attribute("y"))
        assert float(map_svg.get_attribute("data-median-x")) == data["median"]["x"]
        assert float(map_svg.get_attribute("data-median-y")) == data["median"]["y"]
        models_dom = page.locator(".model-mark").evaluate_all(
            "nodes => nodes.map(node => [node.dataset.model, Number(node.dataset.x), Number(node.dataset.y)])"
        )
        assert sorted(models_dom) == sorted([[model["name"], model["x"], model["y"]] for model in data["models"]])
        countries_dom = page.locator("circle.country").evaluate_all(
            "nodes => nodes.map(node => [node.dataset.country, Number(node.dataset.x), Number(node.dataset.y)])"
        )
        assert countries_dom == [[country["name"], country["x"], country["y"]] for country in data["countries"]]
        assert page.locator(".chip").count() == 13
        assert all(page.locator(".chip").evaluate_all("nodes => nodes.map(node => node.innerText)"))
        assert all(value == "true" for value in page.locator(".chip img, .model-mark image, .release-mark image").evaluate_all("nodes => nodes.map(node => node.getAttribute('aria-hidden'))"))
        assert all(float(value) == 8 for value in page.locator(".model-ring").evaluate_all("nodes => nodes.map(node => node.getAttribute('r'))"))
        assert all(width > 10 for width in page.locator(".chip img").evaluate_all("nodes => nodes.map(node => node.getBoundingClientRect().width)"))
        country_before = country_positions(page)

        assert page.locator(".release-panel").count() == 2
        svg_description(page, '.release-panel[data-coordinate="y"] svg', "release-y-svg-title", "release-y-svg-desc")
        svg_description(page, '.release-panel[data-coordinate="x"] svg', "release-x-svg-title", "release-x-svg-desc")
        assert page.locator(".release-mark").count() == len(dated) * 2
        assert page.locator(".frontier-label").count() > 0
        frontier_boxes = page.locator('.frontier-label text').evaluate_all("nodes => nodes.map(node => { const b = node.getBBox(); return [b.x, b.y, b.width, b.height]; })")
        assert all(x >= 96 and y >= 42 and x + width <= 1165 and y + height <= 272 for x, y, width, height in frontier_boxes)
        assert all(a[0] + a[2] <= b[0] or b[0] + b[2] <= a[0] or a[1] + a[3] <= b[1] or b[1] + b[3] <= a[1] for index, a in enumerate(frontier_boxes) for b in frontier_boxes[index + 1:])
        for grok_name in grok_dates:
            assert page.locator(f'[data-release-model="{grok_name}"]').count() == 2
        self_expression_panel = page.locator('.release-panel[data-coordinate="x"]')
        assert self_expression_panel.locator(".scatter-y-label").text_content() == "Survival -> Self-expression ↑"
        qwen = next(model for model in dated if model["name"] == "qwen3.8-flash")
        qwen_self_expression = self_expression_panel.locator('[data-release-model="qwen3.8-flash"]')
        assert float(qwen_self_expression.get_attribute("data-coordinate-value")) == -qwen["x"]
        rendered_slope = float(self_expression_panel.locator("svg").get_attribute("data-fit-slope"))
        expected_slope = -ols_slope(dated, "x") / 86_400_000
        assert abs(rendered_slope - expected_slope) < 1e-18
        for panel in page.locator(".release-panel").all():
            dates = panel.locator(".release-mark").evaluate_all("nodes => nodes.map(node => node.dataset.releaseDate)")
            assert dates == sorted(dates)
            assert panel.locator(".scatter-y-label").count() == 1
            assert "->" in panel.locator(".scatter-y-label").text_content()
            assert panel.locator(".scatter-axis[marker-end]").count() == 1
            assert panel.locator(".release-fit").count() == 1
            assert int(panel.locator("svg").get_attribute("data-fit-n")) == len(dated)
            assert panel.locator(".release-fit line").count() == 1
        page.screenshot(path=OUT / "wvs_react_playwright_release_fit_all_families.png", full_page=True)

        page.get_by_label("Release-panel x axis").select_option("capability")
        assert page.locator('.release-panel[data-coordinate="y"] svg').get_attribute("data-axis-mode") == "capability"
        assert page.locator('.release-mark').count() == len(capability_matched) * 2
        assert all(int(panel.locator("svg").get_attribute("data-fit-n")) == len(capability_matched) for panel in page.locator(".release-panel").all())
        assert all(int(panel.locator("svg").get_attribute("data-omitted-model-count")) == len(data["models"]) - len(capability_matched) for panel in page.locator(".release-panel").all())
        page.screenshot(path=OUT / "wvs_react_playwright_capability_all_families.png", full_page=True)
        page.get_by_role("button", name="qwen", exact=True).click()
        assert all(int(panel.locator("svg").get_attribute("data-fit-n")) == sum(model["family"] != "qwen" for model in capability_matched) for panel in page.locator(".release-panel").all())
        page.screenshot(path=OUT / "wvs_react_playwright_capability_qwen_hidden.png", full_page=True)
        page.get_by_role("button", name="qwen", exact=True).click()
        for family in sorted(families - {"gpt"}):
            page.get_by_role("button", name=family, exact=True).click()
        page.wait_for_timeout(100)
        gpt_capability = sum(model["family"] == "gpt" for model in capability_matched)
        gpt_fit_n = [int(panel.locator("svg").get_attribute("data-fit-n")) for panel in page.locator(".release-panel").all()]
        assert gpt_fit_n == [gpt_capability, gpt_capability], (gpt_fit_n, gpt_capability)
        page.screenshot(path=OUT / "wvs_react_playwright_capability_gpt_only.png", full_page=True)
        for family in sorted(families - {"gpt"}):
            page.get_by_role("button", name=family, exact=True).click()
        page.get_by_label("Release-panel x axis").select_option("release-date")

        page.get_by_role("button", name="qwen", exact=True).click()
        page.wait_for_timeout(100)
        assert map_svg.locator(':scope > g[data-family="qwen"]').get_attribute("display") == "none"
        assert "qwen" not in map_svg.locator("desc").text_content().split("from ", 1)[1]
        assert all(group.get_attribute("display") == "none" for group in page.locator('.release-panel [data-family="qwen"]').all())
        assert country_positions(page) == country_before
        page.screenshot(path=OUT / "wvs_react_root_playwright_qwen_hidden.png", full_page=True)

        page.get_by_role("button", name="qwen", exact=True).click()
        marker = page.locator('[data-model="qwen3.8-flash"]')
        marker.locator(".model-ring").hover()
        page.wait_for_selector("#model-tooltip")
        assert page.locator("#model-tooltip strong").inner_text() == "qwen3.8-flash"
        assert page.locator("#model-tooltip span").all_text_contents() == [
            "Self-expression/Survival: -0.415", "Traditional/Secular-Rational: 0.635", "release 2026-08-26",
        ]
        page.screenshot(path=OUT / "wvs_react_root_playwright_tooltip_hover.png", full_page=True)
        marker.focus()
        assert page.evaluate("document.activeElement.dataset.model") == "qwen3.8-flash"
        assert page.locator("#model-tooltip").is_visible()
        page.screenshot(path=OUT / "wvs_react_root_playwright_keyboard_focus.png", full_page=True)

        release_y_marker = page.locator('.release-panel[data-coordinate="y"] [data-release-model="qwen3.8-flash"]')
        release_y_marker.locator(".model-ring").hover()
        page.wait_for_selector("#release-y-tooltip")
        assert page.locator("#release-y-tooltip strong").inner_text() == "qwen3.8-flash"
        assert page.locator("#release-y-tooltip span").all_text_contents() == ["Secular-Rational: 0.635", "release 2026-08-26"]
        page.screenshot(path=OUT / "wvs_react_root_playwright_release_panel_hover.png", full_page=True)
        release_y_marker.focus()
        assert page.evaluate("document.activeElement.dataset.releaseModel") == "qwen3.8-flash"
        assert page.locator("#release-y-tooltip").is_visible()
        page.screenshot(path=OUT / "wvs_react_root_playwright_release_panel_keyboard_focus.png", full_page=True)
        release_x_marker = page.locator('.release-panel[data-coordinate="x"] [data-release-model="qwen3.8-flash"]')
        release_x_marker.locator(".model-ring").hover()
        page.wait_for_selector("#release-x-tooltip")
        assert release_y_marker.get_attribute("aria-describedby") == "release-y-tooltip"
        assert release_x_marker.get_attribute("aria-describedby") == "release-x-tooltip"
        assert page.locator("#release-x-tooltip strong").inner_text() == "qwen3.8-flash"
        assert page.locator("#release-x-tooltip span").all_text_contents() == ["Self-expression: 0.415", "release 2026-08-26"]
        page.screenshot(path=OUT / "wvs_react_root_playwright_release_self_expression_hover.png", full_page=True)
        for grok_name, grok_date in grok_dates.items():
            grok = next(model for model in dated if model["name"] == grok_name)
            grok_marker = page.locator(f'.release-panel[data-coordinate="y"] [data-release-model="{grok_name}"]')
            grok_marker.locator(".model-ring").hover()
            assert page.locator("#release-y-tooltip strong").inner_text() == grok_name
            assert page.locator("#release-y-tooltip span").all_text_contents() == [
                f"Secular-Rational: {grok['y']:.3f}", f"release {grok_date}",
            ]

        qwen_dated = sum(model["family"] == "qwen" and bool(model["provenance"]["release_created"]) for model in data["models"])
        for family in sorted(families - {"qwen"}):
            page.get_by_role("button", name=family, exact=True).click()
        page.wait_for_timeout(100)
        for family in families:
            expected = "inline" if family == "qwen" else "none"
            assert map_svg.locator(f':scope > g[data-family="{family}"]').get_attribute("display") == expected
        for panel in page.locator(".release-panel").all():
            assert int(panel.locator("svg").get_attribute("data-fit-n")) == qwen_dated
            assert panel.locator(".release-fit").count() == 1
        assert country_positions(page) == country_before
        page.screenshot(path=OUT / "wvs_react_playwright_release_fit_qwen_only.png", full_page=True)

        page.get_by_role("button", name="qwen", exact=True).click()
        page.get_by_role("button", name="muse", exact=True).click()
        page.wait_for_timeout(100)
        for family in families:
            expected = "inline" if family == "muse" else "none"
            assert map_svg.locator(f':scope > g[data-family="{family}"]').get_attribute("display") == expected
        for panel in page.locator(".release-panel").all():
            assert int(panel.locator("svg").get_attribute("data-fit-n")) == 0
            assert panel.locator(".release-fit").count() == 0
            assert panel.locator(".release-fit-unavailable").count() == 1
        assert country_positions(page) == country_before
        page.screenshot(path=OUT / "wvs_react_playwright_release_fit_insufficient.png", full_page=True)

        screenshot(page, f"{BASE}/wvs/react/", "wvs_react_compat_redirect.png")
        page.wait_for_selector("svg .model-mark")
        assert page.url == f"{BASE}/"
        browser.close()

    if errors:
        raise RuntimeError(f"React page errors: {errors}")
    subprocess.run([
        "convert", str(OUT / "wvs_static_playwright.png"), str(OUT / "wvs_react_root_playwright_default.png"),
        "+append", str(OUT / "wvs_static_react_root_playwright_side_by_side.png"),
    ], check=True)
    hashes = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in (
        ROOT / "docs/wvs/wvs_map_data.json",
        ROOT / "docs/index.html",
    )}
    print(json.dumps({
        "root": "React app loaded at /",
        "compatibility": "/wvs/ and /wvs/react/ redirect to the root React app; shared data remains at /wvs/wvs_map_data.json",
        "shared": {"models": 64, "countries": 90, "buffered_hulls": 4, "latest_labels": 13,
                   "numeric_model_country_median_equality": "verified against DOM data attributes"},
        "svg_accessibility": "main map and both release panels have stable title/desc aria-labelledby; descriptions update after family visibility change",
        "qwen_toggle": "clicked, map and dated-panel family groups hidden, country coordinates invariant",
        "tooltip": "map and release-panel pointer hover and focus show panel-specific model name, coordinate, and release date only",
        "release_panels": {"panels": 2, "dated_models": len(dated), "date_order": "DOM order verified; both catalog-dated Grok models rendered in each panel",
                           "ols": "line, n, and R squared recompute from currently visible matched models; the Self-expression panel renders negative stored x, so upward means Self-expression; fewer than two distinct x values hide the fit"},
        "capability_panels": {"matched_models": len(capability_matched), "omitted_models": len(data["models"]) - len(capability_matched),
                              "source": data["capability_x"]["source_url"], "fetched_utc": data["capability_x"]["fetched_utc"],
                              "selector": "enabled; all-family and Qwen-hidden fits checked"},
        "copy": "one short linked WVS sentence above the map; history and axes below it; source credit beside the enabled lower-panel selector; weak descriptive-fit method and code link below the release panels",
        "hashes": hashes,
    }, indent=2))


if __name__ == "__main__":
    main()
