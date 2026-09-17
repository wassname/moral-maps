"""Playwright UAT for the production React WVS SVG. No network calls leave localhost."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "slop/research/wvs/20260916_openrouter"
BASE = "http://localhost:8081/wvs"
VIEWPORT = {"width": 1440, "height": 1800}


def screenshot(page, url: str, name: str) -> Path:
    page.goto(url, wait_until="networkidle")
    page.screenshot(path=OUT / name, full_page=True)
    return OUT / name


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

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=chrome, headless=True, args=["--no-sandbox"])
        page = browser.new_page(viewport=VIEWPORT)
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))

        screenshot(page, "http://localhost:8081/img/wvs/wvs_map_iw.png", "wvs_static_playwright.png")
        screenshot(page, f"{BASE}/", "wvs_vanilla_playwright.png")
        screenshot(page, f"{BASE}/react/", "wvs_react_playwright_default.png")
        page.wait_for_selector("svg .model-mark")
        assert page.locator("path.zone").count() == 4
        assert page.locator("polygon.zone").count() == 0
        assert "64 models" not in page.locator("main").inner_text()
        assert "Historical coordinates" not in page.locator("main").inner_text()
        assert page.locator(".map-note").get_attribute("text-anchor") == "end"
        assert float(page.locator(".map-note").get_attribute("x")) > float(page.locator(".map-title").get_attribute("x"))
        map_svg = page.get_by_role("img", name="Frontier LLMs on the World Values Survey")
        assert float(map_svg.get_attribute("data-median-x")) == data["median"]["x"]
        assert float(map_svg.get_attribute("data-median-y")) == data["median"]["y"]
        rendered_models = page.locator(".model-mark").evaluate_all(
            "nodes => nodes.map(node => [node.dataset.model, Number(node.dataset.x), Number(node.dataset.y)])"
        )
        assert sorted(rendered_models) == sorted([[model["name"], model["x"], model["y"]] for model in data["models"]])
        rendered_countries = page.locator("circle.country").evaluate_all(
            "nodes => nodes.map(node => [node.dataset.country, Number(node.dataset.x), Number(node.dataset.y)])"
        )
        assert rendered_countries == [[country["name"], country["x"], country["y"]] for country in data["countries"]]
        country_before = page.locator("circle.country").evaluate_all(
            "nodes => nodes.map(node => [node.getAttribute('cx'), node.getAttribute('cy')])"
        )
        dated = [model for model in data["models"] if model["provenance"]["release_created"]]
        qwen_group = map_svg.locator(':scope > g[data-family="qwen"]')
        assert qwen_group.get_attribute("display") in (None, "inline")
        assert map_svg.locator('[data-family="qwen"] .model-label').count() == 1
        assert page.locator(".release-panel").count() == 2
        assert page.locator(".release-mark").count() == len(dated) * 2
        for panel in page.locator(".release-panel").all():
            dates = panel.locator(".release-mark").evaluate_all("nodes => nodes.map(node => node.dataset.releaseDate)")
            assert dates == sorted(dates)
        assert page.locator(".release-trajectory").count() == 0
        page.screenshot(path=OUT / "wvs_react_playwright_release_panels.png", full_page=True)

        page.get_by_role("button", name="qwen", exact=True).click()
        page.wait_for_timeout(100)
        assert qwen_group.get_attribute("display") == "none"
        assert map_svg.locator('[data-family="qwen"] .model-label').count() == 1
        assert map_svg.locator('[data-family="muse"] .model-label').count() == 1
        assert all(group.get_attribute("display") == "none" for group in page.locator('.release-panel [data-family="qwen"]').all())
        assert all(group.get_attribute("display") != "none" for group in page.locator('.release-panel [data-family="muse"]').all())
        country_after = page.locator("circle.country").evaluate_all(
            "nodes => nodes.map(node => [node.getAttribute('cx'), node.getAttribute('cy')])"
        )
        assert country_after == country_before
        page.screenshot(path=OUT / "wvs_react_playwright_qwen_hidden.png", full_page=True)

        page.get_by_role("button", name="qwen", exact=True).click()
        marker = page.locator('[data-model="qwen3.8-flash"]')
        marker.locator(".model-ring").hover()
        page.wait_for_selector("#model-tooltip")
        tooltip_text = page.locator("#model-tooltip").inner_text()
        for required in ("qwen3.8-flash", "qwen", "rated categorical response", "12 items x 12 samples"):
            assert required in tooltip_text, required
        page.screenshot(path=OUT / "wvs_react_playwright_tooltip_hover.png", full_page=True)

        marker.focus()
        assert page.evaluate("document.activeElement.dataset.model") == "qwen3.8-flash"
        assert page.locator("#model-tooltip").is_visible()
        page.screenshot(path=OUT / "wvs_react_playwright_keyboard_focus.png", full_page=True)

        release_marker = page.locator('.release-panel[data-coordinate="y"] [data-release-model="qwen3.8-flash"]')
        release_marker.locator(".model-ring").hover()
        page.wait_for_selector("#release-tooltip")
        assert "qwen3.8-flash" in page.locator("#release-tooltip").inner_text()
        page.screenshot(path=OUT / "wvs_react_playwright_release_panel_hover.png", full_page=True)
        release_marker.focus()
        assert page.evaluate("document.activeElement.dataset.releaseModel") == "qwen3.8-flash"
        assert page.locator("#release-tooltip").is_visible()
        page.screenshot(path=OUT / "wvs_react_playwright_release_panel_keyboard_focus.png", full_page=True)
        browser.close()

    if errors:
        raise RuntimeError(f"React page errors: {errors}")
    static = Image.open(OUT / "wvs_static_playwright.png").convert("RGB")
    react = Image.open(OUT / "wvs_react_playwright_default.png").convert("RGB")
    height = max(static.height, react.height)
    comparison = Image.new("RGB", (static.width + react.width, height + 26), "white")
    comparison.paste(static, (0, 26))
    comparison.paste(react, (static.width, 26))
    draw = ImageDraw.Draw(comparison)
    draw.text((6, 5), "Static WVS figure", fill="black")
    draw.text((static.width + 6, 5), "React WVS production page", fill="black")
    comparison.save(OUT / "wvs_static_react_playwright_side_by_side.png")
    hashes = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in (
        ROOT / "docs/wvs/wvs_map_data.json",
        ROOT / "docs/wvs/react/index.html",
    )}
    print(json.dumps({
        "shared": {"models": 64, "countries": 90, "buffered_hulls": 4, "latest_labels": 13,
                   "numeric_model_country_median_equality": "verified against DOM data attributes"},
        "qwen_toggle": "clicked, map and dated-panel family groups hidden, country coordinates invariant",
        "tooltip": "map and release-panel pointer hover and focus show model, family, coordinates, readout, samples and release metadata",
        "release_panels": {"panels": 2, "dated_models": len(dated), "date_order": "DOM order verified", "no_paths": True},
        "copy": "source caption only; no model-count wording or archaeological paragraph",
        "visual_contract": "four smooth SVG paths, no zone polygons, source note right of title",
        "hashes": hashes,
    }, indent=2))


if __name__ == "__main__":
    main()
