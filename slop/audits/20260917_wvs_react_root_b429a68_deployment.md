# GitHub Pages deployment: root React WVS map

- commit: `b429a68`
- verification UTC: 2026-09-17T05:19Z
- root React: <https://wassname.github.io/moral-maps/>
- retained static page: <https://wassname.github.io/moral-maps/wvs/>
- compatible old React path: <https://wassname.github.io/moral-maps/wvs/react/>

## Public evidence

The root HTML contains:

> `<script type="module" crossorigin src="./assets/index-CpA1DfjE.js"></script>`

The fetched root bundle SHA-256 equals the committed bundle SHA-256:

```text
9b0099b258c55b8f328d81e22207c26f08c4262c842ff7c3439a9495c7e90297
```

The fetched shared data SHA-256 equals `docs/wvs/wvs_map_data.json`:

```text
c0b7aa0554ebbf5d819308932e058f4ff6e19d1e817ffebbbe381dbd2d063ffe
```

The old nested path serves its committed redirect:

> `<meta http-equiv="refresh" content="0; url=../../">`

The public static path serves its standalone title and h1:

> `<title>Frontier LLMs on the World Values Survey</title>`
>
> `<h1>Frontier LLMs on the World Values Survey</h1>`

The root HTTP response was `200` from GitHub Pages. This verifies deployed root bundle and shared data bytes, static route presence, and old-path redirect content. It does not independently exercise browser interactions after deployment; local Playwright evidence is in `slop/research/wvs/20260916_openrouter/wvs_react_root_playwright_uat.json`.

-- PI[gpt-5.6-terra]
