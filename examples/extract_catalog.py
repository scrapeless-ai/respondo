"""Run after `python -m pip install .`; all inputs are synthetic and local."""

import json
from pathlib import Path

from respondo import extract_page, json_query


def main() -> None:
    examples = Path(__file__).resolve().parent
    page = extract_page(
        (examples / "catalog.html").read_text(encoding="utf-8"),
        base="https://example.com",
    )
    products = json.loads((examples / "products.json").read_text(encoding="utf-8"))
    assert page["headings"][0] == {"level": 1, "id": "catalog", "text": "Our teas"}
    assert page["links"][0]["href"] == "https://example.com/products/tea"
    assert json_query(products, "products[*].name") == ["Tea", "Coffee"]
    assert json_query(page, "tables[0].rows[*].Name") == ["Tea", "Coffee"]
    print(json.dumps({"page": page, "names": json_query(products, "products[*].name")}, indent=2))


if __name__ == "__main__":
    main()
