"""Sequential, byte-bounded directory processing for the offline CLI.

No recursion or link following. Checks mitigate accidental unsafe inputs; this
is not a sandbox against a concurrently hostile filesystem or parser resource
amplification. Output is staged before publication so budget failures emit none.
"""

import codecs
import errno
import fnmatch
import json
import os
from pathlib import Path
import stat
import sys
import tempfile

from jsonparse import records_to_csv
from jsonparse.records import _strict_loads


MAX_DIRECTORY_ENTRIES = 10000
MAX_RECIPE_BYTES = 1024 * 1024
_CSV_FIELDS = ("source", "status", "result", "error_code", "error_line", "error_column")


class BatchError(Exception):
    """A fixed, source-safe category for a batch-wide failure."""

    def __init__(self, code):
        self.code = code
        super().__init__(code)


def _is_link(info):
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & 0x400)


def _checked_path(path):
    # Do not resolve first: that would hide links/junctions we need to reject.
    path = Path(os.path.abspath(path))
    for parent in reversed(path.parents):
        if _is_link(parent.lstat()):
            raise BatchError("unsafe_path")
    info = path.lstat()
    if _is_link(info):
        raise BatchError("unsafe_path")
    return path, info


def _read(path, limit, budget):
    path, before = _checked_path(path)
    if not stat.S_ISREG(before.st_mode):
        raise BatchError("not_regular_file")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    descriptor = os.open(path, flags)
    with os.fdopen(descriptor, "rb") as stream:
        opened = os.fstat(stream.fileno())
        if not stat.S_ISREG(opened.st_mode) or _is_link(opened) or not os.path.samestat(before, opened):
            raise BatchError("unsafe_path")
        # One extra byte detects growth/overflow without an unbounded read.
        data = stream.read(min(limit, budget[0]) + 1)
    budget[0] -= len(data)
    if budget[0] < 0:
        raise BatchError("total_byte_limit")
    if len(data) > limit:
        raise BatchError("file_too_large")
    return data.decode("utf-8-sig")


def _discover(root, args):
    root, info = _checked_path(root)
    if not stat.S_ISDIR(info.st_mode):
        raise BatchError("not_directory")
    paths = []
    with os.scandir(root) as entries:
        for count, entry in enumerate(entries, 1):
            if count > MAX_DIRECTORY_ENTRIES:
                raise BatchError("directory_entry_limit")
            if not fnmatch.fnmatchcase(entry.name, args.pattern):
                continue
            info = entry.stat(follow_symlinks=False)
            if stat.S_ISDIR(info.st_mode) and not _is_link(info):
                continue
            invalid_name = False
            try:
                entry.name.encode("utf-8")
            except UnicodeError:
                invalid_name = True
            if invalid_name:
                raise BatchError("filename_encoding")
            paths.append(root / entry.name)
            if len(paths) > args.max_files:
                raise BatchError("file_count_limit")
    if not paths:
        raise BatchError("empty_selection")
    return root, sorted(paths, key=lambda path: path.name)


def _output_path(value, root):
    if value is None:
        return None
    path = Path(os.path.abspath(value))
    parent, info = _checked_path(path.parent)
    if not stat.S_ISDIR(info.st_mode) or any(os.path.samefile(root, ancestor) for ancestor in (parent, *parent.parents)):
        raise BatchError("unsafe_output_path")
    if os.path.lexists(path):
        raise BatchError("output_exists")
    return path


def _error(exc):
    if isinstance(exc, BatchError):
        if exc.code == "total_byte_limit":
            raise exc
        return {"code": exc.code}
    if isinstance(exc, json.JSONDecodeError):
        return {"code": "invalid_json", "line": exc.lineno, "column": exc.colno}
    for kind, code in ((UnicodeError, "encoding_error"), (OSError, "io_error"),
                       (RecursionError, "nesting_limit"), (KeyError, "missing_pointer")):
        if isinstance(exc, kind):
            return {"code": code}
    return {"code": "invalid_input"}


def _row(path, args, extract, budget):
    result, error = None, None
    try:
        result = extract(_read(path, args.max_file_bytes, budget), args)
    except (BatchError, UnicodeError, OSError, RecursionError, KeyError, ValueError, TypeError) as exc:
        error = _error(exc)
    return {"source": path.name, "status": "error" if error else "ok", "result": result, "error": error}


def _json(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":"))


def _chunks(row, args, header):
    if args.format == "jsonl":
        # Incremental encoding avoids materializing the entire output string.
        yield from json.JSONEncoder(ensure_ascii=False, allow_nan=False, separators=(",", ":")).iterencode(row)
        yield "\n"
    else:
        error = row["error"] or {}
        cells = dict(zip(_CSV_FIELDS, (row["source"], row["status"], _json(row["result"]),
                                      error.get("code", ""), error.get("line", ""), error.get("column", ""))))
        encoded = records_to_csv([cells], delimiter=args.delimiter, escape_formulas=not args.raw_csv)
        yield encoded if header else encoded.split("\n", 1)[1]


def _closed_pipe(error, output):
    if isinstance(error, BrokenPipeError):
        return True
    # Windows CRT reports a closed anonymous pipe as EINVAL, not EPIPE. Limit
    # this exception to output pipes so ordinary file/device errors stay errors.
    if sys.platform == "win32" and error.errno == errno.EINVAL:
        try:
            return stat.S_ISFIFO(os.fstat(output.fileno()).st_mode)
        except (AttributeError, OSError, ValueError):
            pass
    return False


def _pipe_output(output, operation, *args):
    try:
        operation(*args)
    except OSError as exc:
        if _closed_pipe(exc, output):
            raise BrokenPipeError() from None
        raise


def _copy(spool, output):
    spool.seek(0)
    if hasattr(output, "buffer"):
        for chunk in iter(lambda: spool.read(65536), b""):
            _pipe_output(output, output.buffer.write, chunk)
        _pipe_output(output, output.buffer.flush)
    else:
        decoder = codecs.getincrementaldecoder("utf-8")()
        for chunk in iter(lambda: spool.read(65536), b""):
            _pipe_output(output, output.write, decoder.decode(chunk))
        _pipe_output(output, output.write, decoder.decode(b"", final=True))
        _pipe_output(output, output.flush)


def _stage(spool, row, args, header, total):
    for chunk in _chunks(row, args, header):
        encoded = chunk.encode("utf-8")
        total += len(encoded)
        if total > args.max_output_bytes:
            raise BatchError("output_byte_limit")
        spool.write(encoded)
    return total


def run_batch(args, extract, stdout):
    """Emit outcome envelopes; return 1 on per-file failures, 0 if all succeed."""
    try:
        root, paths = _discover(args.file, args)
        destination = _output_path(args.output, root)
        budget = [args.max_total_bytes]
        for name in ("fields", "patch"):
            if getattr(args, name) is not None:
                value = _strict_loads(_read(getattr(args, name), MAX_RECIPE_BYTES, budget))
                setattr(args, "_" + name + "_data", value)
        total, failed = 0, False
        with tempfile.SpooledTemporaryFile(max_size=1024 * 1024, mode="w+b") as spool:
            for index, path in enumerate(paths):
                row = _row(path, args, extract, budget)
                offset = spool.tell()
                try:
                    total = _stage(spool, row, args, index == 0, total)
                except (UnicodeError, ValueError, TypeError, RecursionError) as exc:
                    # Discard only this incomplete row; budgets/I/O remain global.
                    spool.seek(offset)
                    spool.truncate()
                    row = {"source": path.name, "status": "error", "result": None, "error": _error(exc)}
                    total = _stage(spool, row, args, index == 0, total)
                failed = failed or row["status"] == "error"
            if destination is None:
                _copy(spool, stdout)
            else:
                # Recheck immediately before exclusive creation; never truncate.
                _output_path(destination, root)
                with destination.open("x", encoding="utf-8", newline="") as output:
                    _copy(spool, output)
        return 1 if failed else 0
    except BrokenPipeError:
        raise
    except (UnicodeError, OSError, RecursionError, KeyError, ValueError, TypeError) as exc:
        # Never expose paths, source values or raw parser/OS exceptions.
        code = _error(exc)["code"]
    raise BatchError(code) from None
