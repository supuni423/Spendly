# Spendly — AI-Powered Shopping Assistant

A Chrome extension that reads the product you're looking at, compares its price across other stores, checks it against your own spending history, and tells you whether to buy it, wait, or consider it — with a natural-language explanation from an LLM that is never allowed to invent a number.

## Why this exists

Most "AI shopping assistant" demos pipe everything through a model and hope for the best — including the numbers. Spendly is built the other way around: **every number the user sees (savings %, budget impact, match confidence, the recommendation itself) is computed deterministically by the backend before the LLM is ever called.** The LLM's only job is to explain a decision it didn't make, constrained to a `{reasoning, summary}` schema with no room to state a price, a percentage, or a category. If the LLM is unavailable, misconfigured, or times out, a templated fallback produces the same explanation from the same facts — the user experience degrades gracefully, the numbers never do.

## Architecture

```
Chrome Extension (Manifest V3, React + TypeScript)
  └─ Content script detects the current product (schema.org/Open Graph,
     or a real site-specific adapter — e.g. Amazon's actual DOM)
  └─ Popup calls the backend, renders the result
        │
        ▼
FastAPI backend (Python)
  ├─ Deterministic pipeline: discover candidates → match product →
  │  normalize price → calculate savings → decide recommendation
  ├─ Shopping agent: Gemini function-calling, tool-restricted to reading
  │  facts the backend already computed — never calculating anything
  └─ Auth (JWT + bcrypt), rate limiting, audit logging, IDOR-safe queries
        │
        ▼
PostgreSQL (users, purchases, products, price history, audit log)
```

Price sources are pluggable behind a `ProductSource` interface — adding a new one (a new store, eventually a real retailer API) requires zero changes to the matching or comparison engine. Today's sources are a 5-store, 40-product synthetic catalog (`backend/sources/mock/catalog.json`) rather than live retailers — real external price integration is gated behind actual confirmed API/data-access permission, which hasn't been sought yet. This is a portfolio/demo project, not a shipped product; see `backend/README.md` for the honest list of what real-world use would still require.

## Try it

- **Backend**: see `backend/README.md` for setup, tests, and (if you want to try a hosted version) deploy instructions.
- **Extension**: see `extension/README.md` for building it and trying it against either a real product page or the bundled "Fake Mall" demo storefront.

<!-- Demo screenshot/GIF: add one here once you have it — e.g. the popup showing a real analysis result, or a quick screen recording of analyzing a product on the Fake Mall. -->

## Stack

Chrome Extension (Manifest V3), TypeScript, React, Vite · Python, FastAPI, SQLAlchemy, Alembic, PostgreSQL · Gemini API
