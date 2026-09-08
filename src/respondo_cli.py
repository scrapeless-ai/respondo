"""Local HTML/JSON/XML extraction and record interchange; no network or AI calls."""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Optional

from _respondo_version import __version__
from respondo_batch import _closed_pipe

from htmlparse import (
    extract_headings,
    extract_images,
    extract_link_details,
    extract_meta,
    extract_page,
    extract_tables,
    get_text,
    html_to_markdown,
    select_html,
    extract_records,
)
from jsonparse import (
    csv_to_records, find_all_json, iter_jsonl, json_flatten, json_merge_patch,
    json_pointer, json_project, json_query, jsonl_dumps, records_to_csv,
)
from jsonparse.records import _strict_loads
from webparse import normalize_url, parse_feed, parse_sitemap


_MODES = ("page", "text", "markdown", "links", "headings", "meta", "images", "tables", "json", "query",
          "select", "records", "pointer", "flatten", "merge", "project", "jsonl", "csv", "feed", "sitemap", "url")
_LIST_MODES = {"links", "headings", "images", "tables", "json", "query", "select", "records", "project", "jsonl", "csv"}


def _json_file(path: str):
    return _strict_loads(Path(path).read_text(encoding="utf-8-sig"))


def _recipe(args, name):
    cached = "_" + name + "_data"
    return getattr(args, cached) if hasattr(args, cached) else _json_file(getattr(args, name))


def _json_array(content: str):
    value = _strict_loads(content)
    if not isinstance(value, list):
        raise ValueError("expected a JSON array of records")
    return value


def _arguments(argv):
    parser = argparse.ArgumentParser(
        prog="respondo",
        description="Extract and reshape local HTML, JSON, XML and CSV. Reads stdin by default; never fetches URLs.",
    )
    parser.add_argument(
        "mode",
        choices=_MODES,
        help="extraction or transformation to perform",
    )
    parser.add_argument("file", nargs="?", default="-", help="UTF-8 input file, or - for stdin")
    parser.add_argument("--base", help="base URL for relative links and image sources")
    parser.add_argument("--version", action="version", version="respondo " + __version__)
    parser.add_argument("--path", help="JSONPath for query or JSON Pointer for pointer mode")
    parser.add_argument("--selector", help="CSS selector subset for select/records modes")
    parser.add_argument("--fields", help="local JSON file containing record field recipes or projection pointers")
    parser.add_argument("--patch", help="local JSON merge-patch file")
    parser.add_argument("--skip-blank", action="store_true", help="ignore blank JSON Lines input lines")
    parser.add_argument("--delimiter", default=",", help="one-character CSV delimiter (default comma)")
    parser.add_argument("--raw-csv", action="store_true", help="disable formula-like string escaping for trusted CSV consumers")
    parser.add_argument("--drop-fragment", action="store_true", help="remove URL fragment in url mode")
    parser.add_argument("--remove-tracking", action="store_true", help="remove known tracking parameters in url mode")
    parser.add_argument("--sort-query", action="store_true", help="sort query pairs in url mode")
    parser.add_argument("--compact", action="store_true", help="emit JSON on one line")
    parser.add_argument("--batch", action="store_true", help="process immediate files in a directory, sequentially")
    parser.add_argument("--pattern", help="batch basename glob, case-sensitive (default *)")
    parser.add_argument("--output", help="batch output file outside the input directory; must not exist")
    for name in ("max-files", "max-file-bytes", "max-total-bytes", "max-output-bytes"):
        parser.add_argument("--" + name, type=int, help="positive batch resource limit; see documentation for defaults")
    parser.add_argument(
        "--format", choices=("json", "text", "jsonl", "csv"), default="json",
        help="output JSON, plain text, or JSON Lines/CSV for list-valued modes",
    )
    args = parser.parse_args(argv)
    limits = {"max_files": 1000, "max_file_bytes": 10 * 1024 * 1024,
              "max_total_bytes": 100 * 1024 * 1024, "max_output_bytes": 32 * 1024 * 1024}
    if args.batch:
        if args.file == "-" or args.format not in {"jsonl", "csv"}:
            parser.error("--batch requires a directory and --format jsonl or csv")
        args.pattern = "*" if args.pattern is None else args.pattern
        if not args.pattern or args.pattern in {".", ".."} or any(c in args.pattern for c in ("/", "\\", "\x00")):
            parser.error("--pattern must be a nonempty basename glob")
        for name, default in limits.items():
            value = getattr(args, name)
            if value is not None and not 0 < value < sys.maxsize:
                parser.error("batch limits must be positive integers below the platform maximum")
            setattr(args, name, default if value is None else value)
    elif args.pattern is not None or args.output is not None or any(getattr(args, name) is not None for name in limits):
        parser.error("pattern, output and resource limits require --batch")
    for option, modes in {"path": {"query", "pointer"}, "selector": {"select", "records"},
                          "fields": {"records", "project"}, "patch": {"merge"}}.items():
        value = getattr(args, option)
        if args.mode in modes and value is None:
            parser.error(f"{args.mode} mode requires --{option}")
        if args.mode not in modes and value is not None:
            parser.error(f"--{option} is not available for {args.mode} mode")
    if args.format == "text" and args.mode not in {"text", "markdown", "url"}:
        parser.error("--format text requires text, markdown or url mode")
    if not args.batch and args.format in {"jsonl", "csv"} and args.mode not in _LIST_MODES:
        parser.error("JSON Lines/CSV output requires a list-valued mode")
    if args.compact and args.format != "json":
        parser.error("--compact only applies to JSON output")
    if args.skip_blank and args.mode != "jsonl":
        parser.error("--skip-blank only applies to jsonl input")
    if args.raw_csv and args.format != "csv":
        parser.error("--raw-csv only applies to CSV output")
    if args.delimiter != "," and args.mode != "csv" and args.format != "csv":
        parser.error("--delimiter only applies to CSV input/output")
    if (args.drop_fragment or args.remove_tracking or args.sort_query) and args.mode != "url":
        parser.error("URL cleanup options require url mode")
    return parser, args


def _extract(content, args):
    extractors = {
        "page": lambda: extract_page(content, args.base),
        "text": lambda: get_text(content),
        "markdown": lambda: html_to_markdown(content),
        "links": lambda: extract_link_details(content, args.base),
        "headings": lambda: extract_headings(content),
        "meta": lambda: extract_meta(content),
        "images": lambda: extract_images(content, args.base),
        "tables": lambda: extract_tables(content),
        "json": lambda: find_all_json(content),
        "query": lambda: json_query(_strict_loads(content), args.path),
        "pointer": lambda: json_pointer(_strict_loads(content), args.path),
        "flatten": lambda: json_flatten(_strict_loads(content)),
        "merge": lambda: json_merge_patch(_strict_loads(content), _recipe(args, "patch")),
        "project": lambda: json_project(_json_array(content), _recipe(args, "fields")),
        "select": lambda: select_html(content, args.selector),
        "records": lambda: extract_records(content, args.selector, _recipe(args, "fields")),
        "jsonl": lambda: list(iter_jsonl(content, skip_blank=args.skip_blank)),
        "csv": lambda: csv_to_records(content, delimiter=args.delimiter),
        "feed": lambda: parse_feed(content, args.base),
        "sitemap": lambda: parse_sitemap(content, args.base),
        "url": lambda: normalize_url(content.strip(), base=args.base, drop_fragment=args.drop_fragment,
                                     remove_tracking=args.remove_tracking, sort_query=args.sort_query),
    }
    return extractors[args.mode]()


def _serialize(result, args):
    if args.format == "text":
        return result + "\n"
    if args.format == "csv":
        return records_to_csv(result, delimiter=args.delimiter, escape_formulas=not args.raw_csv)
    if args.format == "jsonl":
        return jsonl_dumps(result)
    return json.dumps(result, ensure_ascii=False, allow_nan=False, indent=None if args.compact else 2,
                      separators=(",", ":") if args.compact else None) + "\n"


def main(argv: Optional[List[str]] = None) -> int:
    """Read a UTF-8 local file/stdin and write one complete result (no partial rows)."""
    parser, args = _arguments(argv)

    try:
        if args.batch:
            from respondo_batch import BatchError, run_batch
            try:
                return run_batch(args, _extract, sys.stdout)
            except BatchError as exc:
                parser.exit(1, "respondo: batch " + exc.code.replace("_", " ") + "\n")
        if args.file == "-":
            if hasattr(sys.stdin, "buffer"):
                content = sys.stdin.buffer.read().decode("utf-8-sig")
            else:
                content = sys.stdin.read().lstrip("\ufeff")
        else:
            content = Path(args.file).read_text(encoding="utf-8-sig")

        output = _serialize(_extract(content, args), args)
        encoded = output.encode("utf-8")
        try:
            if hasattr(sys.stdout, "buffer"):
                sys.stdout.buffer.write(encoded)
                sys.stdout.buffer.flush()
            else:
                print(output, end="", flush=True)
        except OSError as exc:
            if _closed_pipe(exc, sys.stdout):
                raise BrokenPipeError() from None
            raise
    except json.JSONDecodeError as exc:
        parser.exit(1, f"respondo: invalid JSON at line {exc.lineno}, column {exc.colno}\n")
    except UnicodeError:
        parser.exit(1, "respondo: input or output encoding error; use UTF-8\n")
    except BrokenPipeError:
        # Prevent the interpreter's final stdout flush from raising EPIPE again.
        with open(os.devnull, "w") as sink:
            os.dup2(sink.fileno(), sys.stdout.fileno())
        return 0
    except OSError as exc:
        parser.exit(1, f"respondo: I/O error: {exc.strerror}\n")
    except RecursionError:
        parser.exit(1, "respondo: input nesting exceeds supported limits\n")
    except KeyError:
        parser.exit(1, "respondo: JSON pointer does not resolve\n")
    except (ValueError, TypeError):
        # urllib/stdlib exceptions can embed untrusted source values. Never print
        # arbitrary exception text from parsers, even when a local helper is safe.
        parser.exit(1, f"respondo: invalid input or configuration for {args.mode} mode; see --help\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
