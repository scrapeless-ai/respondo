"""Run with python -I after installation; never add the checkout to sys.path."""

import importlib.metadata
import json
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile

import respondo as r


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def main():
    require(sys.flags.isolated, "Run this check with python -I")
    require(len(sys.argv) == 2, "Pass the expected release version")
    version = sys.argv[1]
    package_path = Path(r.__file__).resolve()
    require(package_path.is_relative_to(Path(sys.prefix).resolve()), "Imported checkout instead of installed package")
    require(r.__version__ == importlib.metadata.version("respondo") == version, "Version mismatch")
    require(not importlib.metadata.requires("respondo"), "Unexpected runtime dependencies")
    require(len(r.__all__) == len(set(r.__all__)), "Duplicate public export")
    require(all(hasattr(r, name) for name in r.__all__), "Missing public export")
    require(r.list_providers()["openai"] == "OPENAI_MODEL", "Model variable discovery failed")
    try:
        r.parse_ai("x", "y", model="", strict=True)
    except r.AIError as error:
        require(error.code == "missing_model", "Wrong strict configuration error")
    else:
        raise RuntimeError("Missing model was not rejected before network I/O")

    html = '<article><h2>Tea</h2><a href="/tea">Shop</a></article>'
    rows = r.extract_records(html, "article", {"name": "h2", "url": {"selector": "a", "attr": "href"}})
    require(rows == [{"name": "Tea", "url": "/tea"}], "Record extraction failed")
    require(r.select_html(html, "article > h2")[0]["text"] == "Tea", "Selector failed")
    require(r.extract_page(html)["headings"][0]["text"] == "Tea", "Page extraction failed")
    require(r.json_pointer(rows, "/0/name") == "Tea", "JSON Pointer failed")
    require(r.json_query(rows, "$[*].name") == ["Tea"], "JSON query failed")
    require(r.json_flatten(rows)["/0/url"] == "/tea", "Flattening failed")
    require(r.json_merge_patch(rows[0], {"url": None}) == {"name": "Tea"}, "Merge patch failed")
    require(r.json_project(rows, {"label": "/name"}) == [{"label": "Tea"}], "Projection failed")
    require(list(r.iter_jsonl(r.jsonl_dumps(rows))) == rows, "JSON Lines failed")
    require(r.csv_to_records(r.records_to_csv(rows)) == rows, "CSV failed")
    require(r.normalize_url("HTTPS://EXAMPLE.TEST:443") == "https://example.test/", "URL normalization failed")
    require(r.update_url_query("https://example.test/", {"page": 2}) == "https://example.test/?page=2", "Query update failed")
    require(r.parse_feed('<rss version="2.0"><channel><title>Tea</title></channel></rss>')["title"] == "Tea", "Feed failed")
    require(r.parse_sitemap('<urlset><url><loc>https://example.test/</loc></url></urlset>')["entries"][0]["loc"] == "https://example.test/", "Sitemap failed")
    response = r.Response(200, {"Content-Type": "text/html; charset=utf-8", "Retry-After": "2"}, html.encode())
    require(response.raise_for_status().select_html("h2")[0]["text"] == "Tea", "Response extraction failed")
    require(response.retry_after() == 2, "Response header failed")

    command = Path(sys.executable).with_name("respondo.exe" if sys.platform == "win32" else "respondo")
    for argv in ([str(command)], [sys.executable, "-I", "-m", "respondo"]):
        completed = subprocess.run(argv + ["--version"], capture_output=True, text=True, encoding="utf-8", check=True, timeout=15)
        require(completed.stdout.strip() == "respondo " + version, "CLI version failed")
        completed = subprocess.run(argv + ["query", "--path", "$[*].name"], input=json.dumps(rows),
                                   capture_output=True, text=True, encoding="utf-8", check=True, timeout=15)
        require(json.loads(completed.stdout) == ["Tea"], "CLI query failed")
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary).resolve()
            (directory / "page.html").write_text(html, encoding="utf-8")
            completed = subprocess.run(argv + ["text", str(directory), "--batch", "--format", "jsonl"],
                                       capture_output=True, text=True, encoding="utf-8", check=True, timeout=15)
            outcome = json.loads(completed.stdout)
            require(outcome["source"] == "page.html" and outcome["status"] == "ok", "Installed batch failed")
            require(outcome["result"] == "Tea Shop", "Installed batch result failed")
    root = Path(__file__).resolve().parents[1]
    runpy.run_path(str(root / "examples" / "extraction_pipeline.py"), run_name="__main__")
    print("PASS: installed version, exports, AI configuration, 14 pipeline APIs, Response, both CLI entry points, batch and example")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
