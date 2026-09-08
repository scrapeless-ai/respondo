"""Run after installing this checkout: python examples/extraction_pipeline.py."""

import json
from pathlib import Path

from respondo import (
    Response, csv_to_records, extract_records, iter_jsonl, json_flatten,
    json_merge_patch, json_pointer, json_project, jsonl_dumps, normalize_url,
    parse_feed, parse_sitemap, records_to_csv, select_html, update_url_query,
)


HERE = Path(__file__).resolve().parent
html = (HERE / "cards.html").read_text(encoding="utf-8")
fields = json.loads((HERE / "card-fields.json").read_text(encoding="utf-8"))
records = extract_records(html, ".product", fields)
assert [row["name"] for row in records] == ["Green tea", "Coffee"]
assert select_html(html, ".product > h2")[0]["text"] == "Green tea"
assert json_pointer(records, "/0/tags/1") == "Loose leaf"
assert json_flatten(records)["/0/name"] == "Green tea"
assert json_merge_patch(records[0], {"tags": None}) == {key: value for key, value in records[0].items() if key != "tags"}
assert list(iter_jsonl(jsonl_dumps(records))) == records

columns = json_project(records, {"Product": "/name", "Price": "/price"})
csv = records_to_csv(columns)
assert csv_to_records(csv) == columns
url = normalize_url(records[0]["url"], base="https://example.test")
assert update_url_query(url, {"page": 2}) == "https://example.test/products/tea?page=2"
assert parse_feed((HERE / "feed.xml").read_bytes())["entries"][0]["title"] == "Green tea"
assert len(parse_sitemap((HERE / "sitemap.xml").read_bytes())["entries"]) == 2

response = Response(200, {"Content-Type": "text/html; charset=utf-8", "Link": '</next>; rel=next'}, html.encode())
assert response.raise_for_status().extract_records(".product", fields) == records
assert response.links("https://example.test/")[0]["url"] == "https://example.test/next"
print(csv, end="")
