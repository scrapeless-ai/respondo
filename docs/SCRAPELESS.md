# Respondo in your Scrapeless workflow

**Collect with Scrapeless. Extract, transform and export with Respondo.**

Respondo is the local Python layer for turning web responses into useful records.
It works on content you already have: HTML strings, JSON documents and response
bodies. The package does not make requests to Scrapeless or manage API credentials.

## 1. Collect the content

Use your existing [Scrapeless workflow](https://www.scrapeless.com/en) to retrieve
the page or dataset. Follow the [platform documentation](https://docs.scrapeless.com/)
for the product you use; credentials and network access belong to that collection
step. Pass the returned HTML into Respondo, or save it as a local UTF-8 file.

The example below uses a synthetic fixture included in this repository. It does
not contact Scrapeless or require an account:

```bash
respondo records examples/cards.html --selector .product --fields examples/card-fields.json --format csv
```

## 2. Extract repeatable records

Keep the selectors in a reusable recipe so your collection and extraction logic
can evolve independently:

```python
from respondo import extract_records, normalize_url, records_to_csv

def product_csv(html, page_url):
    records = extract_records(html, '.product', {
        'name': {'selector': 'h2', 'required': True},
        'price': '.price',
        'url': {'selector': 'a', 'attr': 'href'},
    })
    for record in records:
        if record['url'] is not None:
            record['url'] = normalize_url(record['url'], base=page_url)
    return records_to_csv(records)
```

The recipe validates required matches; it does not validate business rules or
convert prices to numbers. Validate records before using them in an application.
URL normalization does not make a URL safe to fetch.

## 3. Connect to an existing browser page

When your browser library provides an asynchronous `page.content()` method,
hand the resulting HTML to the same local extraction function:

```python
async def products_from_page(page):
    html = await page.content()
    return product_csv(html, page.url)
```

This adapter assumes you already own an authenticated browser page. It does not
create a session, configure a CDP endpoint or install a browser SDK. Respondo's
runtime remains standard-library-only.

## Choose the output for the next step

| Consumer | Respondo output |
|:---------|:----------------|
| Python application | Dictionaries from `extract_records` or `extract_page` |
| Data pipeline | JSON Lines with `jsonl_dumps` / `--format jsonl` |
| Spreadsheet or import job | CSV with `records_to_csv` / `--format csv` |
| Text indexing | Page text or Markdown with `extract_page` / `html_to_markdown` |

See [API contracts and limits](API.md) and [security boundaries](../SECURITY.md).
Optional AI parsing is a separate feature that transmits input to its selected
provider. Ordinary extraction and every CLI mode stay local.

For a directory of saved responses, use bounded, sequential batch extraction:

```bash
respondo records responses/ --batch --pattern '*.html' --selector .product --fields examples/card-fields.json --format jsonl --output results.jsonl
```

Keep the new output file outside `responses/`. Each row contains the source
filename, status, extracted result and optional sanitized error. CSV output uses
the same file-outcome structure with JSON in the result cell. See the
[batch contract](API.md#batch-directory-processing) for limits and exit codes.
AI consumers must configure their provider's `*_MODEL` variable or pass `model=`;
there are no built-in model choices. Use `strict=True` to handle `AIError` codes.
