# Releasing Respondo by Scrapeless

This is a preparation checklist, not permission to publish. The current source
describes **0.6.0, unreleased on PyPI**. The package and import name remain
`respondo`; the repository is `scrapeless-ai/respondo`.

## Establish the source of truth

- This repository is distributed as a single parentless publication snapshot.
  The full development history is retained separately. Do not push a development
  branch or its ancestry into this publication repository.
- Before any future snapshot replacement, obtain explicit maintainer approval
  for the exact target, verify the selected account, default branch and protection,
  and back up the current remote refs/history. Review and validate the complete
  snapshot in a separate checkout. Use a lease bound to the verified remote SHA;
  stop if the branch changes or protection disallows the operation.
- Preserve existing MIT attribution and keep publication identity scoped to the
  publication checkout. Never change global Git identity or copy credentials.
- Confirm ownership of the PyPI project and availability of the intended version.
  A README badge or an unsuccessful page lookup is not proof of ownership.
- Review the official logo, product wording, existing MIT notice and source
  provenance in `assets/README.md`. Branding does not alter the code license.
- Keep the issue/checklist current. No release, deploy or publication is performed
  by the CI workflow in this repository.

## Local verification

Use Python 3.12 for the locked release tools. The runtime has no third-party
dependencies. Create the environment in an empty location you own:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install --require-hashes -r requirements-release.txt
.venv/bin/python scripts/run_tests.py
.venv/bin/python -m coverage erase
.venv/bin/python -m coverage run scripts/run_tests.py
.venv/bin/python -m coverage combine
.venv/bin/python -m coverage report
```

On Windows, use `.venv\Scripts\python.exe` instead. `scripts/run_tests.py` runs
unittest discovery **and** both legacy script suites; discovery alone is incomplete.
AI provider tests are synthetic mocks, not live service checks. Coverage includes
CLI subprocesses and has an 80% threshold. Test supported Python versions in CI;
Python 3.9 is retained for compatibility, not recommended for hostile inputs.

Build into a fresh output directory to avoid mixing release versions:

```bash
.venv/bin/python -m build --no-isolation --outdir dist
.venv/bin/python -m twine check --strict dist/*
.venv/bin/python scripts/verify_dist.py dist --version 0.6.0
```

The default `build` command creates an sdist, then builds the wheel **from that
sdist**, checking that the source archive can reproduce a package. The verifier
checks required modules/docs, metadata, zero runtime dependencies, archive paths,
links, local/credential-file exclusions and archive-size bounds. It prints SHA-256
checksums. It is not a substitute for reviewing source and history for secrets.
Do not treat checksums as proof of authorship.

Install the exact wheel without package-index access into a new virtualenv, then
run the isolated smoke check from outside the source tree. Absolute paths below
are placeholders for your checkout, artifact and clean environment:

```bash
python3.12 -m venv /path/to/respondo-smoke
/path/to/respondo-smoke/bin/python -m pip install --no-index --no-deps /path/to/dist/respondo-0.6.0-py3-none-any.whl
cd /path/outside/the/checkout
/path/to/respondo-smoke/bin/python -I /path/to/respondo/scripts/smoke_installed.py 0.6.0
```

Repeat from a fresh sdist extraction/build when validating a release candidate.
The smoke check verifies the import came from the environment, not `src/`, and
exercises exports, new APIs, Response, installed CLI, module CLI and examples.
Preview the README in GitHub light/dark themes and confirm local image/doc links.
The self-contained PyPI description does not depend on private repository images.

## CI and dependency maintenance

`.github/workflows/ci.yml` tests Python 3.9–3.14 on Linux plus 3.12 on Windows
and macOS. Its separate build job runs coverage, validates both distributions,
and smoke-tests the installed wheel before uploading the release-candidate files.
Actions are pinned to reviewed commit SHAs; the workflow has read-only repository
permissions and does not receive publishing credentials. A local run does not
prove that hosted CI has run.

Regenerate the Python-3.12 release-tool lock after reviewing dependency changes:

```bash
uv pip compile requirements-release.in --python-version 3.12 --generate-hashes --output-file requirements-release.txt --no-cache
```

The lock was generated for the Linux release job; other platforms only need the
standard library to run the source test suite. Do not install release-tool
dependencies into the runtime package.

## Publication: maintainer-authorized follow-up only

1. Complete human review, source publication and hosted CI. Check that the
   release assets are built from the exact reviewed commit.
2. Verify project ownership/version availability on TestPyPI and PyPI separately.
3. Prefer a [PyPI Trusted Publisher](https://docs.pypi.org/trusted-publishers/using-a-publisher/)
   bound to the exact repository, workflow and protected environment. Require
   environment approval and grant `id-token: write` only to a future publishing job.
   Do not commit tokens or pass them in command arguments.
4. With explicit authorization, upload the **already validated** artifacts to
   TestPyPI, smoke-test their installation, then promote those same artifacts to
   PyPI. Do not quietly rebuild after validation.
5. Verify public package metadata, installation, repository links, banner and
   release notes. Record the commit, filenames, checksums and actual verification
   output in the release and tracking issue.

## Rollback

Before a source snapshot replacement, retain and verify a local mirror or bundle
of the prior remote history. Restoring it is a separate maintainer-authorized
operation: verify the current target and use an explicit SHA-specific lease.
Keep development-history backups separate from the publication checkout.

Before PyPI publication, retain the previous candidate. After PyPI publication,
package versions cannot be replaced: prepare a corrected version, or request
authorization to yank a defective release. Never remove another session's
worktree or delete release evidence. Keep the existing MIT notice throughout.
