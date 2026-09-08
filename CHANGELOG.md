# Changelog

## 0.6.0 — Unreleased on PyPI

- Resolve AI models from explicit `model=` or provider `*_MODEL` environment
  variables; remove built-in model choices. `list_providers()` now returns model
  variable names. Existing callers relying on model defaults must configure one.
- Forward schemas in every AI adapter and add opt-in `AIError` via `strict=True`,
  with sanitized configuration/HTTP/timeout/JSON failures and finite JSON parsing.
- Add sequential directory `--batch` extraction, deterministic JSONL/CSV file
  outcomes, byte/count budgets, link checks and exclusive output-file creation.
- Present Respondo as a Scrapeless product, with the official logo, consistent
  README styling and a guide to local extraction in Scrapeless workflows.
- Fix explicit UTC timestamp parsing without changing unzoned local-time behavior.

- Add `select_html` CSS-subset matching and `extract_records` reusable field recipes.
- Add JSON Pointer lookup, pointer-based flattening, independent merge patching,
  record projection, lazy JSON Lines input, JSON Lines output and CSV interchange.
- Add conservative URL normalization/query updates and local RSS/Atom/sitemap
  extraction with DTD, input-size, depth and resolved-base limits.
- Add `HTTPStatusError`, explicit Response decoding, status checking, Retry-After,
  Link headers and charset-aware HTML/JSON convenience methods.
- Expand the CLI to 21 modes, JSONL/CSV output, recipe files and `--version`.
- Fix inherited Python 3.9 import compatibility, quoted Content-Type parsing,
  and Gemini authentication in request URLs; provider tests use synthetic mocks.
- Add the unified test entry point, publication guides, CI/artifact validation,
  contributor templates and a self-contained PyPI description.

- Add `json_query` with dot/bracket paths, negative indexes, object/array wildcards,
  JSON-escaped quoted keys, and predictable empty-match behavior.
- Add `extract_headings` and `extract_link_details` with document-order results,
  relative URL resolution, and non-content element filtering.
- Add `extract_page` to collect text, metadata, headings, links, images and tables
  into a stable JSON-serializable result.
- Add the `respondo` CLI and `python -m respondo` for local files and stdin, with
  compact JSON, plain-text output, and explicit errors.
- Add synthetic examples and stdlib behavioral tests covering the new APIs and CLI.
- Add a generated Respondo/Scrapeless banner using the official logo as reference,
  keep its vector source, and use repository-local README artwork.
- Update package repository links to the user-provided `scrapeless-ai/respondo` target.

This source snapshot is based on the supplied 0.5.0 source archive, with the
Scrapeless branding, extraction features and reliability improvements listed
above. Version 0.6.0 has not been published to PyPI.
