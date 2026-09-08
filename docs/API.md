# Extraction pipelines

All functions below use Python's standard library. Local extraction and CLI APIs
accept caller-supplied data without browsers, downloads, AI calls or credentials.
The separate optional AI API makes authenticated requests to a chosen provider.
Import from `respondo`; the original API remains available.

## HTML selection and records

```python
from respondo import extract_records, select_html

html = '<article class="card"><h2>Tea</h2><a href="/tea">Details</a></article>'
select_html(html, '.card > h2')
# [{'tag': 'h2', 'attrs': {}, 'text': 'Tea'}]
extract_records(html, '.card', {
    'name': 'h2',
    'url': {'selector': 'a', 'attr': 'href'},
    'tags': {'selector': '.tag', 'many': True},
})
# [{'name': 'Tea', 'url': '/tea', 'tags': []}]
```

Selectors support ASCII tags, `*`, `.class`, `#id`, `[attr]`, `[attr=value]`,
quoted attribute values, descendant spaces, child `>`, and comma groups.
Results are deduplicated in document order, not selector-group order. Tag and
attribute names are case-insensitive; class, ID and attribute values are exact.
CSS escapes, pseudo-classes, sibling combinators and other attribute operators
are unsupported and raise `ValueError`, even on empty documents. Chains have
at most 32 components. This is **not a complete CSS or HTML5 DOM implementation**.

Field recipes:

| Option | Behavior |
| --- | --- |
| String shorthand | Equivalent to `{'selector': string}` |
| `selector` | Search descendants; ancestors cannot escape the current item. Omit to read the item itself. |
| `attr` | Read an attribute instead of text. Missing attributes are skipped; empty values remain. |
| `many: True` | Always return a list, including `[]` when absent. |
| `default` | Copied fallback for a missing scalar, default `None`; not allowed with `many`. |
| `required: True` | Raise if no values match. Empty strings count as values, not missing fields. |

Scalar fields take the first available value. Unknown options and invalid rules
fail before matching. Text preserves inline word boundaries, normalizes whitespace,
adds block spacing, and omits script/style/template/noscript text even when a
descendant is selected. Hidden attributes and CSS visibility are not evaluated.
Extracted attributes/URLs are raw data: escape/sanitize for their eventual use.

## JSON lookup and transformation

| Function | Contract |
| --- | --- |
| `json_query(obj, path)` | JSONPath-style subset; always returns matches as a list. See the README for syntax. |
| `json_pointer(obj, pointer, default=...)` | RFC 6901 string pointer; `''` selects root; `/a~1b/0` escapes `/`. Missing path raises `KeyError` unless default is explicit. URI fragments (`#/...`) are unsupported. |
| `json_flatten(obj)` | JSON Pointer → leaf mapping. Keeps nulls and empty containers; scalar/empty roots use `''`. Numeric object keys and array indexes are ambiguous, so this format is intentionally **not invertible**. |
| `json_merge_patch(target, patch)` | RFC 7396 semantics: object members merge, null deletes, arrays/scalars replace wholesale. Returns independent data and never modifies either input. |
| `json_project(records, fields, default=None)` | Output column → JSON Pointer mapping per input object record. Missing paths receive a copied default; explicit null remains null. |

```python
from respondo import json_merge_patch, json_pointer, json_project

rows = [{'name': 'Tea', 'price': {'amount': 3}}, {'name': 'Coffee'}]
assert json_pointer(rows, '/0/price/amount') == 3
assert json_project(rows, {'label': '/name', 'cost': '/price/amount'}) == [
    {'label': 'Tea', 'cost': 3}, {'label': 'Coffee', 'cost': None},
]
assert json_merge_patch({'a': 1, 'b': [1]}, {'a': None, 'b': [2]}) == {'b': [2]}
```

Lookup APIs return references; merge/projection outputs own their values.
Flatten and merge require finite, JSON-compatible values and reject cycles.
Keep recursive JSON inputs reasonably bounded; these are in-memory utilities.

Standards: [JSON Pointer](https://www.rfc-editor.org/info/rfc6901/),
[JSON Merge Patch](https://www.rfc-editor.org/info/rfc7396/).

## JSON Lines and CSV

`iter_jsonl(text_or_line_iterable, skip_blank=False)` lazily yields values and
never closes caller-owned streams. Open files with UTF-8. Blank lines are errors
unless opted out; errors name the physical line without echoing its contents.
The library rejects a BOM, NaN, Infinity and numbers overflowing the finite float
range. `jsonl_dumps(records)` returns UTF-8-encodable compact JSON Lines with a
final LF, or `''` for no records. It materializes its output.

`records_to_csv(records, fieldnames=None, delimiter=',', escape_formulas=True)`
materializes rows, discovers columns in first-seen order, or selects explicit
columns. It uses CRLF rows and standard CSV quoting. Missing/null values become
empty cells, nested values compact JSON, and booleans `true`/`false`.

Formula-like **strings and headers** receive an apostrophe by default. Numeric
negative values stay numeric. This intentionally changes some values; use
`escape_formulas=False` only for trusted machine interchange. It is a mitigation,
not a guarantee across every spreadsheet. Escape according to your destination.

`csv_to_records(text, delimiter=',')` returns only string values. It accepts a
leading BOM, skips blank physical rows and rejects duplicate headers/ragged
rows. Parsing follows `csv.reader(strict=True)`: quotes inside unquoted cells
are literal. It does not infer numeric types or remove formula-prefix apostrophes.
CSV does not preserve the distinction between null, absent and empty strings.

## URLs, feeds and sitemaps

`normalize_url(url, base=None, drop_fragment=False, remove_tracking=False,
sort_query=False)` normalizes HTTP(S) scheme, IDNA hostname, default ports and
an empty path. Paths, percent-encoded separators and query spelling are preserved
unless a query transformation is requested. Fragment removal and tracking removal
are opt-in. Tracking names are `utm_*`, `fbclid`, `gclid` and `msclkid`.

`update_url_query(url, updates, base=None)` replaces all occurrences of updated
keys and appends replacements in mapping order. Lists/tuples generate repeated
keys; `None`/`[]` remove a key. Unrelated pair order, duplicates and blank values
are retained. Query transforms regenerate percent encoding and reject invalid
UTF-8 encoded values rather than corrupting them. These helpers reject embedded
credentials, controls, invalid ports, percent-encoded hosts and IPvFuture literals.
They do not enforce an SSRF policy or establish that a URL is safe to fetch.

`parse_feed(xml, base=None, max_bytes=10*1024*1024)` accepts text or bytes and
normalizes RSS 2.0/Atom to:

```text
format, title, link, description, language, entries
  entry: id, title, link, summary, content, published, updated,
         authors[], categories[], enclosures[{url, type, length}]
```

Dates and enclosure lengths remain strings; absent scalars are `''`, collections
are `[]`. Atom picks the first alternate link and inherits feed authors if entry
authors are absent. HTML/CDATA remain untrusted markup; embedded XHTML is
reserialized with namespace prefixes. RSS content/DC extension fields are supported.

`parse_sitemap(xml, base=None, max_bytes=10*1024*1024)` returns `{type, entries}`.
URL-set entries contain `loc`, `lastmod`, `changefreq`, `priority`; sitemap-index
entries contain `loc`, `lastmod`. Missing locations are errors. Extensions are
ignored. Index locations are returned, never downloaded recursively.

Both XML APIs honor inherited `xml:base`, preserve entry order, reject DTDs even
in UTF-16 input, and enforce depth ≤128, each resolved base ≤8192 characters and
cumulative resolved bases ≤8,388,608 characters. Standard namespaces and unqualified variants
are accepted. These are extractors, not full schema validators. Use a patched
Python/Expat runtime and application-level input/time limits for hostile data.

References: [sitemaps](https://www.sitemaps.org/protocol.html),
[RSS](https://www.rssboard.org/rss-specification),
[Atom](https://www.rfc-editor.org/info/rfc4287/),
[Python XML security](https://docs.python.org/3/library/xml.html#xml-security).

## Response helpers

Construct `Response(status, headers, body, raw_headers=None)` from your own HTTP
client. Pass repeated header pairs through `raw_headers`; Respondo never fetches.

| Method | Behavior |
| --- | --- |
| `.decode(encoding=None, errors='strict')` | Explicit encoding, then Content-Type charset, then UTF BOM, then UTF-8. Does not decompress. Legacy `.text` remains UTF-8 with replacement. |
| `.raise_for_status()` | Raises `HTTPStatusError` for 400–599; otherwise returns self. Exception contains `.status` and `.response`, but its message omits body/headers. |
| `.retry_after(now=None)` | Nonnegative seconds or `None` for invalid/absent metadata. Caller-supplied `now` must be timezone-aware. No sleep/retry; apply your own maximum delay. |
| `.links(base=None)` | Ordered `{url, rel, params}` records; quoted delimiters and repeated headers work. First duplicate parameter wins; valueless extensions use `''`. Malformed syntax raises. |
| `.extract_page(base=None)`, `.select_html(selector)`, `.extract_records(item_selector, fields)` | Use strict charset-aware decoding with the corresponding HTML APIs. |
| `.json_query(path)` | Apply JSONPath-style selection to `.json()`. |

Link `anchor` and extended parameters such as `title*` remain raw; anchor context
is not applied. This is metadata extraction, not a full RFC 8288 interpreter.
References: [Web Linking](https://httpwg.org/specs/rfc8288.html),
[Retry-After](https://httpwg.org/specs/rfc9110.html#field.retry-after).

## CLI recipes

```bash
respondo records examples/cards.html --selector .product --fields examples/card-fields.json --format jsonl
respondo records examples/cards.html --selector .product --fields examples/card-fields.json --format csv
respondo select examples/cards.html --selector '.product > h2'
respondo pointer examples/products.json --path /products/0/name
respondo flatten examples/products.json
respondo feed examples/feed.xml
respondo sitemap examples/sitemap.xml
respondo --version
```

`merge --patch file.json` accepts one complete JSON input and a local patch file.
`project --fields columns.json` requires a JSON **array**, with pointer mappings
in the fields file. `jsonl --skip-blank` and `csv --delimiter ';'` import records.
List-valued modes can emit `--format jsonl` or `--format csv`; CSV requires object
records. `--raw-csv` disables the formula-prefix mitigation. `url` reads one URL;
`--drop-fragment`, `--remove-tracking`, `--sort-query` are optional cleanup flags.

Single-file commands read a complete UTF-8 file/stdin before output, accepting a leading BOM
even for JSON Lines (unlike `iter_jsonl`). It is not a streaming CLI. It serializes
all results before writing, so data errors do not produce partial result rows.
Exit codes: 0 success/empty matches, 1 data or I/O failure, 2 invalid arguments.
Diagnostics never echo source document contents; JSON syntax errors include
line/column, while other parser failures give a generic mode-specific message.

## Batch directory processing

Add `--batch` with a directory and `--format jsonl` or `--format csv` to any mode.
Required mode options still apply. There is no stdin, recursion, network or AI.
`--pattern '*.html'` matches basenames case-sensitively; the default is `*`.
Directories are skipped. Selected filenames must be UTF-8 encodable; unsupported
names cause a batch-wide `filename_encoding` error before processing any file.
Selected links/junctions and non-regular files produce
per-file errors; links in the input/config/output path are rejected.

Files are processed sequentially in sorted filename order. JSONL contains one
envelope per file:

```json
{"source":"page.html","status":"ok","result":{"title":"Example"},"error":null}
{"source":"bad.html","status":"error","result":null,"error":{"code":"encoding_error"}}
```

An empty or null extraction is still `ok`. CSV columns are `source`, `status`,
`result`, `error_code`, `error_line`, `error_column`; decode the `result` cell as
JSON. This is an outcome report, not flattened dataset rows. Formula-like source
filenames are escaped by default; `--raw-csv` preserves them for trusted consumers.

| Limit | Default | Option |
|:------|:--------|:-------|
| Selected files | 1,000 | `--max-files` |
| Bytes per input file | 10 MiB | `--max-file-bytes` |
| Total bytes read, including recipes and failed files | 100 MiB | `--max-total-bytes` |
| Encoded output bytes | 32 MiB | `--max-output-bytes` |
| Entries inspected in one directory, including unmatched entries | 10,000 | fixed |
| Each fields/patch recipe | 1 MiB | fixed |

All configurable limits are positive integers below `sys.maxsize`. Reads are bounded with a one-byte
overflow probe; that byte counts toward total input. BOMs and multibyte characters
count as their UTF-8 bytes. Recipes are loaded once. One oversize file is a
`file_too_large` outcome; exceeding the total, output, count or discovery limit
aborts the whole batch without publishing its staged output. Empty selection is
an error. UTF-8, JSON syntax (with line/column), missing pointers, I/O, nesting and
other parser failures become sanitized per-file codes; no raw document appears
in an error. Successful results intentionally contain the extracted source data.

Output stages in a temporary spool (memory up to 1 MiB, then disk) before stdout
or `--output NEW_FILE`. Output files must not exist and must be outside the input
directory. Staging prevents partial output from parsing/budget failures, not from
disk/device failures during final publication. Exit codes are 0 for all files
successful, 1 for any file/batch failure, 2 for invalid arguments.

These are byte/I/O limits, not hard process RAM/CPU limits: each file and its
extracted result are materialized, and parsers/CSV encoding can amplify memory.
Use OS process limits for untrusted large workloads. Link and identity checks
are defensive checks, not a sandbox against concurrent hostile filesystem edits.

## Optional AI configuration and errors

`parse_ai` and `parse_ai_json` choose `model=` first, otherwise the provider's
uppercase `*_MODEL` variable. There is no built-in model. `list_providers()` maps
provider names to those variable names. API keys use the corresponding
`*_API_KEY` variables or explicit `api_key=`; inject secrets securely at runtime.

Legacy calls return `""` / `None` on configuration, transport or decoding failure.
Keyword-only `strict=True` raises public `AIError`, with `.code` and optional
`.status_code`. Configuration codes: `unknown_provider`, `invalid_input`,
`invalid_model`, `missing_model`, `missing_api_key`, `invalid_schema`. Request
codes: `authentication` (401/403), `rate_limit` (429), `http_error`, `timeout`,
`connection`, `invalid_response`, `request_error`. JSON decoding uses
`invalid_json` and rejects nonfinite numbers, including exponent overflow.
Strict mode must be a boolean. Errors omit bodies, URLs and credential values.

All ten adapters forward dictionary schemas, using either provider fields or
prompt instructions. Neither a provider's structured-output support nor local
schema validation is guaranteed. `parse_ai_json` validates JSON syntax, not
schema conformance; any valid JSON root (including null) can be returned. A null
success is indistinguishable from legacy failure, so use strict mode when needed.
Requests keep the existing 120-second transport timeout and do not retry.
Authenticated requests refuse all redirects, including same-origin redirects,
and report them as `http_error` rather than forwarding credentials.
