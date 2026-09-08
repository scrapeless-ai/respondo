# Respondo by Scrapeless

Parse the web. Shape the data.

A zero-runtime-dependency Python extraction toolkit from [Scrapeless](https://www.scrapeless.com/en)
for text, HTML, JSON, HTTP responses,
RSS/Atom feeds and sitemaps. Includes a local command-line interface. Python 3.9+.

Use Scrapeless to retrieve web content, then use Respondo to extract records,
transform fields and export JSON, JSON Lines or CSV locally. Respondo does not
fetch URLs or include a Scrapeless API client.

[Repository](https://github.com/scrapeless-ai/respondo) ·
[Scrapeless platform docs](https://docs.scrapeless.com/)

## Install

```bash
python -m pip install respondo
```

From a source checkout, use `python -m pip install .`. This documentation describes
the 0.6 feature set; check `respondo --version` after installation.

## Extract repeated records

```python
from respondo import extract_records, records_to_csv

html = '<article><h2>Tea</h2><a href="/tea">Details</a></article>'
records = extract_records(html, 'article', {
    'name': 'h2',
    'url': {'selector': 'a', 'attr': 'href'},
})
assert records == [{'name': 'Tea', 'url': '/tea'}]
print(records_to_csv(records), end='')
```

Selectors support tags, classes, IDs, attribute equality/existence, descendant
and child combinators, and comma groups. Unsupported CSS syntax raises errors.

## Transform JSON

```python
from respondo import json_pointer, json_project, json_query, json_merge_patch

data = {'products': [{'name': 'Tea', 'price': 3}]}
assert json_query(data, '$.products[*].name') == ['Tea']
assert json_pointer(data, '/products/0/price') == 3
assert json_project(data['products'], {'label': '/name'}) == [{'label': 'Tea'}]
assert json_merge_patch({'a': 1}, {'a': None, 'b': 2}) == {'b': 2}
```

Also included: JSON Pointer flattening; lazy JSON Lines reading; JSON Lines
serialization; CSV import/export; URL normalization/query updates; RSS/Atom and
sitemap extraction; HTTP charset decoding, status errors, Retry-After and Link
headers; page summaries, forms, tables, metadata, Markdown and text utilities.

## Command line

```bash
respondo --help
respondo --version
respondo page page.html
respondo select page.html --selector 'article > h2'
respondo query data.json --path '$.items[*]' --format jsonl
respondo csv data.csv --format jsonl
respondo feed feed.xml
respondo sitemap sitemap.xml
respondo page responses/ --batch --pattern '*.html' --format jsonl
```

Files and stdin are UTF-8. Output defaults to JSON; supported list modes can emit
JSON Lines or CSV. All CLI operations are local and make no network requests.
Batch mode processes immediate directory files sequentially and emits one
result/error envelope per file. It bounds file counts and input/output bytes;
optional `--output` creates a new file outside the input directory exclusively.
See the source API guide for limits, CSV envelope columns and exit codes.

## Boundaries

Respondo is an extractor, not a browser, sanitizer, crawler, or authentication
system. The CSS/JSONPath subsets are documented in the source API guide. Extracted
HTML and URLs remain untrusted. XML DTDs are rejected and resource limits apply;
keep Python/Expat patched. CSV formula-prefix mitigation changes some string
values and is not a universal spreadsheet guarantee.

Optional AI parsing sends inputs to the selected third-party provider and requires
credentials supplied securely at runtime. Schema enforcement varies by provider;
validate returned data yourself. Models come from explicit `model=` or provider
`*_MODEL` variables; there is no built-in model selection. `list_providers()` maps
provider names to model variable names. Opt into `strict=True` for sanitized
`AIError` categories instead of legacy empty failures. `decode_jwt` decodes only and does not verify
signatures. MD5/SHA-1/base64 helpers are not password protection.

The source distribution includes examples, tests, CONTRIBUTING.md, SECURITY.md,
RELEASING.md and docs/API.md. Run all tests with `python scripts/run_tests.py`.
Licensed under MIT; third-party brand marks retain their owners' rights.
