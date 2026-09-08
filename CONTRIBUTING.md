# Contributing

Keep Respondo dependency-free at runtime, compatible with Python 3.9+, and
backward-compatible unless a documented release explicitly changes a contract.

## Local development

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e .
python scripts/run_tests.py
python examples/extraction_pipeline.py
```

Tests themselves need only the standard library and can run without installation.
The unified runner executes unittest discovery **and** the two legacy script
suites; discovery alone misses the legacy checks. Tests use synthetic data and
mocked AI calls, never production data or real provider credentials.

## Changes

1. Work on a focused branch and preserve existing work.
2. Add failing behavioral tests before implementing a feature or fix.
3. Keep public functions typed and document inputs, output shape, missing values,
   failure behavior, resource limits and unsupported syntax.
4. Export public APIs through the relevant package and `src/respondo.py`.
5. Update `docs/API.md`, examples and `CHANGELOG.md` when contracts change.
6. Run the full suite and build/installation checks in `RELEASING.md`.
7. Open one reviewable PR with motivation, test evidence, compatibility notes and
   rollback guidance. Do not put real credentials or private inputs in the PR.

Use clear names, small focused modules, and explicit failures for new APIs. Do not
add runtime downloads, import-time network requests, eval-based selectors, or
undocumented fallback behavior. Never claim full CSS/JSONPath/browser support
for a deliberately limited parser. Keep transformations deterministic and avoid
mutating caller input unless explicitly documented.

`src/_respondo_version.py` is the single version source for the package and CLI.
Development build/coverage tools are separate from runtime dependencies; the
release lock targets Python 3.12. Python 3.9 is retained for compatibility but is
end-of-life upstream; use a currently maintained Python for untrusted inputs.

See `SECURITY.md` for private reporting and safe handling of extracted content.
