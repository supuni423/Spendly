# Spendly — extension

Chrome MV3 extension: React + TypeScript + Vite, a popup that calls the
real backend and renders its analysis, and a content script that detects
the current product — either generically (schema.org/Open Graph) or via a
real site-specific adapter (Amazon's actual DOM). See the root `README.md`
for the overall architecture.

## Develop

```bash
npm install
npm run dev
```

Then in Chrome: `chrome://extensions` → enable Developer mode → **Load
unpacked** → select `extension/dist` (run `npm run build` once first so
`dist/` exists; `npm run dev` rebuilds it on save via CRXJS's HMR).

## Try it locally

The content script is injected on demand (via the `activeTab` permission)
each time you open the popup — it never runs automatically on page load,
and there's no per-domain allowlist in `manifest.json`. Open any page with
Open Graph `product` tags or schema.org `Product` JSON-LD (a real product
page, or the bundled fake store below) and open the popup; Spendly reads
that page's product on that gesture.

`test-page/` is a small "Fake Mall" (`npm run serve:test-page`, then open
`http://localhost:8765/`) with five separately-browsable stores — two
clothing (StyleHub, TrendCart) and three electronics (TechMart, QuickBuy,
ByteBazaar) — 20 products each, category-tagged with an icon thumbnail.
Every clothing product is sold at both clothing stores, and every
electronics product at all three electronics stores, each at a different
price, so analyzing anything shows a genuine multi-store comparison.

These pages are **generated**, not hand-written: `backend/sources/mock/catalog.json`
is the single source of truth for every product/store/price, loaded by
both the backend (`backend/sources/mock/mock_source.py`) and
`npm run generate:test-pages` (`extension/scripts/generate-test-pages.mjs`),
which rebuilds all of `test-page/` from it. So the storefronts you click
through and the prices Spendly actually computes can never drift apart —
edit `catalog.json` and regenerate rather than hand-editing the HTML.

## Pointing at a deployed backend

By default the extension talks to `http://localhost:8001`. To build a
copy that talks to a deployed backend instead:

```bash
VITE_API_BASE_URL=https://your-deployed-url npm run build
```

This updates both where the extension actually fetches from
(`src/api/apiClient.ts`) and `manifest.json`'s `host_permissions`
(`vite.config.ts`) from the same variable, so they can't drift out of
sync. See `backend/README.md`'s Deploy section for the backend side.

## Icons

`public/icons/icon{16,48,128}.png` are generated from `design/source-icon.png`
via `npm run generate:icons` (uses `sharp` to resize/crop to each size).
To use different artwork, replace `design/source-icon.png` and re-run that
script, then `npm run build`.
