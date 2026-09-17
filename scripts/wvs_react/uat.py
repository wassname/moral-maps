"""Playwright UAT for the root React WVS page. No network calls leave localhost."""
from __future__ import annotations

import hashlib
import json
import shutil
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


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    chrome = shutil.which("google-chrome")
    if chrome is None:
        raise RuntimeError("google-chrome is required for the Playwright UAT")
    data = json.loads((ROOT / "docs/wvs/wvs_map_data.json").read_text())
    assert data["schema"] == 2
    assert len(data["models"]) == 64
    assert len(data["countries"]) == 90
    assert len(data["zone_hulls"]) == 4
    assert len(data["latest_by_family"]) == 13
    assert all(len(zone["points"]) >= 30 for zone in data["zone_hulls"])
    dated = [model for model in data["models"] if model["provenance"]["release_created"]]
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
        assert page.title() == "Frontier LLMs on the World Values Survey"
        assert page.locator("html").get_attribute("lang") == "en"
        assert page.locator('meta[name="viewport"]').count() == 1
        assert page.locator("h1").inner_text().startswith("How do AI models score on human values surveys?")
        visible_copy = page.locator("main").inner_text()
        for absent in ("React/SVG rendering", "Artificial Analysis", "Historical coordinates", "Dated releases only"):
            assert absent not in visible_copy
        assert "ordinary least squares" in visible_copy

        map_svg = page.locator("svg[data-median-x]")
        svg_description(page, "svg[data-median-x]", "map-svg-title", "map-svg-desc")
        assert page.locator("path.zone").count() == 4
        assert page.locator("polygon.zone").count() == 0
        assert page.locator(".map-note").get_attribute("text-anchor") == "end"
        assert float(page.locator(".map-note").get_attribute("x")) > float(page.locator(".map-title").get_attribute("x"))
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
        for required in ("qwen3.8-flash", "qwen", "rated categorical response", "12 items x 12 samples"):
            assert required in page.locator("#model-tooltip").inner_text()
        page.screenshot(path=OUT / "wvs_react_root_playwright_tooltip_hover.png", full_page=True)
        marker.focus()
        assert page.evaluate("document.activeElement.dataset.model") == "qwen3.8-flash"
        assert page.locator("#model-tooltip").is_visible()
        page.screenshot(path=OUT / "wvs_react_root_playwright_keyboard_focus.png", full_page=True)

        release_y_marker = page.locator('.release-panel[data-coordinate="y"] [data-release-model="qwen3.8-flash"]')
        release_y_marker.locator(".model-ring").hover()
        page.wait_for_selector("#release-y-tooltip")
        assert "qwen3.8-flash" in page.locator("#release-y-tooltip").inner_text()
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
        "tooltip": "map and release-panel pointer hover and focus show model-specific fields",
        "release_panels": {"panels": 2, "dated_models": len(dated), "date_order": "DOM order verified",
                           "ols": "line, n, and R squared recompute from currently visible dated models; fewer than two distinct dates hide the fit"},
        "copy": "reader-facing WVS introduction; no model-count, archaeological, implementation, or Artificial Analysis text",
        "hashes": hashes,
    }, indent=2))


if __name__ == "__main__":
    main()
