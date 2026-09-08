# Respondo 0.6 release verification

## Scope and user journeys

Derived from the request to expand Respondo and prepare it for publication under
Scrapeless. This document records local verification of the source snapshot;
hosted CI and PyPI publication require separate evidence. Preserve the `respondo`
import/command, MIT notice and zero runtime dependencies.

- Extract repeated HTML records using supported CSS selectors and field recipes.
- Transform nested JSON, normalize URLs, parse feeds/sitemaps and export datasets.
- Decode HTTP responses and inspect status, Retry-After and pagination headers.
- Run equivalent local workflows through the installed CLI without network calls.
- Configure AI models from runtime environment variables, forward schemas and
  expose opt-in sanitized failures; all provider tests remain offline.
- Process local directories sequentially with per-file JSONL/CSV outcomes,
  resource limits, safe paths and explicit failure semantics.
- Install complete, inspected wheel/source distributions with Scrapeless-facing
  documentation and reproducible build checks.

## Test-first checkpoints

Test-first development records are preserved in the separate development
history, not in this parentless publication snapshot. The behavioral guarantees
and their executable regression tests remain part of the snapshot:

| Guarantee | Test target |
|:----------|:------------|
| JSON Pointer, transforms, JSONL and CSV | test_data_pipeline.py |
| HTML selectors and record recipes | test_selectors.py |
| CSV and JSONL edge cases | test_data_pipeline.py |
| Bounded selector matching and hidden text | test_selectors.py |
| URL and bounded XML extraction | test_webparse.py |
| Response decoding and HTTP metadata | test_response_tools.py |
| URL/XML boundaries, Gemini URL safety, Python 3.9 import | test_webparse.py, test_release_safety.py |
| Quoted charset and HTTP date handling | test_response_tools.py |
| Expanded CLI workflows | test_cli_pipeline.py |
| Fail-closed legacy-suite runner | test_release_safety.py |
| Source-safe CLI errors and projection shape | test_cli_pipeline.py |
| Distribution safety verifier | test_distribution.py |
| UTF-8 regardless of host locale; CLI metadata required | test_cli_pipeline.py, test_distribution.py |
| Explicit UTC independent of local timezone | test_timestamps.py |
| Environment models, schema forwarding, strict AI failures | test_ai_reliability.py, test_ai_contracts.py |
| Bounded directory batch extraction | test_batch_cli.py |
| AI Unicode, finite numeric JSON and HTTP cleanup | test_ai_reliability.py |
| Per-file serialization, alias containment, numeric limits, empty schemas | test_batch_cli.py, test_ai_reliability.py |
| Authenticated redirects rejected | test_ai_redirects.py |
| Windows closed pipes and filename/descriptor boundaries | test_batch_cli.py, test_features.py |
| Spool read failures remain errors, not closed pipes | test_batch_cli.py |

Recent RED observations were concrete: the distribution verifier module did not
exist; a mocked cp1252 default raised UnicodeEncodeError before CLI invocation;
an archive without console metadata was accepted; UTC input incorrectly invoked
the local timestamp converter. The same targets passed after their respective
fixes. Additional AI tests characterize inherited behavior using synthetic
transport/key-lookup mocks; they are not claims of live provider compatibility.

The native Windows run reproduced `OSError: [Errno 22] Invalid argument` on a
closed stdout pipe, followed by interpreter exit 120. Output-only conversion
fixed the regression without treating regular-file or spool I/O errors as
success. Synthetic redirect tests exercise the actual urllib redirect machinery
without opening a socket, for 301/302/303/307/308 and multiple destination types.

## Full-suite results

The pre-publication matrix below tested the same runtime, test and build inputs
included in this snapshot; subsequent publication edits changed documentation
only. Linux runs used a clean source archive, not an installed source checkout.
Command: `python scripts/run_tests.py` on each
interpreter below. Every Linux run returned exit 0 with **171 unittest methods +
367 original script checks + 38 bot-protection checks = 576 checks**. No Linux
tests or script suites were skipped.

| Python | Platform | Result |
|:-------|:---------|:-------|
| 3.9.25 | Linux x86-64 | PASS |
| 3.10.20 | Linux x86-64 | PASS |
| 3.11.15 | Linux x86-64 | PASS |
| 3.12.3 | Linux x86-64 | PASS |
| 3.13.13 | Linux x86-64 | PASS |
| 3.14.5 | Linux x86-64 | PASS |
| 3.14.3 | Native Windows | PASS; 3 platform-specific skips |

Windows ran the same full suite directly on the project: 168 executed unittest
methods and all 405 legacy checks passed. The three skips are POSIX raw filenames,
FIFO creation and a symlink test where the host does not permit link creation.

The Python 3.12 run used `python -m coverage run scripts/run_tests.py`, then
`python -m coverage combine` and `python -m coverage report --format=total --precision=2`.
Result: **82.61% combined statement/branch coverage**, above the 80% gate. Coverage
includes CLI subprocesses. Batch processing is **96.81%**, the AI module is
**96.42%** under mocks, and the CLI is **94.15%**. The new selector/record,
data-transform, URL/XML, page and HTTP-header modules are above 90%.
Legacy HTML/Response helper coverage is lower and remains a maintenance area.
The release scripts are validated by archive tests and isolated install checks;
they are not included in the runtime `src/` coverage percentage.

## Release and presentation checks

- `python -m build --no-isolation` successfully creates an sdist and builds its
  wheel from that sdist; use a fresh output directory for every candidate.
- `python -m twine check --strict` passes for wheel and source metadata.
- `python scripts/verify_dist.py <dist-directory> --version 0.6.0` verifies
  module/doc inclusion, metadata, no runtime dependencies, safe archive paths,
  link/file-type exclusions and size limits before printing SHA-256 checksums.
- Installing the built wheel with `--no-index --no-deps` into a fresh environment,
  followed by `python -I scripts/smoke_installed.py 0.6.0` from outside the source
  tree, passes public exports, pipeline APIs, Response, console/module CLI and
  the executable example. It also checks environment-model discovery, strict
  missing-model failure without a request, and actual batch results from both
  installed entry points. The original isolation check fails without installation.
- CI YAML parses and specifies SHA-pinned actions, read-only repository
  permissions and a six-version Python matrix plus Windows/macOS jobs.
- Eighteen local documentation/image links resolve after excluding sample code.
- Corrected README JWT and timestamp examples were executed. UTC round-trips
  were also checked under UTC and Europe/Madrid by independent review.
- Local light/dark README previews were visually inspected. The README uses a
  raster banner generated with the official logo as reference; the exact official
  SVG is preserved separately in `assets/`. The light-canvas banner is readable
  in both themes.
- Independent standards and specification reviews have no remaining material
  findings. Source/history sanitation found only synthetic test credential
  patterns, preserved MIT attribution and no actual credentials.
- Independent candidate archive review confirms all 26 Python modules match the
  committed source; new tests/docs are in the sdist, with no machine configuration,
  credentials, unsafe archive entries, caches or unrelated build output.

Final candidate filenames/checksums and authoritative source commit are recorded
alongside the delivered archives and in the tracking handoff, avoiding a
self-referential checksum inside an archive. Rebuild after any source change.

## Remaining operator checks

Hosted GitHub CI, native macOS execution, live AI-provider requests and PyPI
ownership/publication are not proven by these local checks. Consult the workflow
run for the exact published commit for hosted results. Follow
[RELEASING.md](../../RELEASING.md) before a separately authorized PyPI publication;
version 0.6.0 remains unreleased there. Native Windows verification above is local
evidence, not a hosted-CI result.
