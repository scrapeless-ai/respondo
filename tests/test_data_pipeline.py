"""Contracts for local JSON transformation and record interchange."""

import copy
import io
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import respondo as r


class PointerTests(unittest.TestCase):
    def test_root_and_escaped_keys(self):
        data = {"a/b": {"m~n": [False, None]}, "": 7, "~1": 8}
        self.assertIs(r.json_pointer(data, ""), data)
        self.assertIs(r.json_pointer(data, "/a~1b/m~0n/0"), False)
        self.assertIsNone(r.json_pointer(data, "/a~1b/m~0n/1"))
        self.assertEqual(r.json_pointer(data, "/"), 7)
        self.assertEqual(r.json_pointer(data, "/~01"), 8)

    def test_missing_raises_or_returns_explicit_default(self):
        for data, path in [({}, "/x"), ([], "/0"), ([0], "/-"),
                           ([0], "/01"), ([0], "/-1"), ([0], "/١"), (None, "/x")]:
            with self.subTest(path=path):
                with self.assertRaises(KeyError):
                    r.json_pointer(data, path)
                self.assertEqual(r.json_pointer(data, path, default="missing"), "missing")
        self.assertEqual(r.json_pointer({"01": 9}, "/01"), 9)

    def test_invalid_pointer_even_with_default(self):
        for path in ["x", "#/x", "/~", "/~2", "/missing/~bad"]:
            with self.subTest(path=path), self.assertRaises(ValueError):
                r.json_pointer({}, path, default=None)
        with self.assertRaises(TypeError):
            r.json_pointer({}, None)


class TransformTests(unittest.TestCase):
    def test_flatten_preserves_empty_values_and_escapes_keys(self):
        data = {"a/b": [{"~": 1}, {}, []], "": None}
        expected = {"/a~1b/0/~0": 1, "/a~1b/1": {}, "/a~1b/2": [], "/": None}
        self.assertEqual(r.json_flatten(data), expected)
        for value in [{}, [], None, False, 2, ""]:
            self.assertEqual(r.json_flatten(value), {"": value})
        for pointer, value in r.json_flatten(data).items():
            self.assertEqual(r.json_pointer(data, pointer), value)

    def test_flatten_rejects_non_json_and_cycles(self):
        cyclic = []
        cyclic.append(cyclic)
        for data in [{1: "bad"}, {"bad": float("nan")}, {"bad": object()}, cyclic]:
            with self.subTest(kind=type(data)), self.assertRaises((TypeError, ValueError)):
                r.json_flatten(data)

    def test_merge_patch_deletes_merges_and_copies(self):
        target = {"title": "Old", "author": {"name": "Ada", "email": "a@example.test"}, "tags": [1]}
        patch = {"title": "New", "author": {"email": None}, "tags": [2], "missing": None}
        before = copy.deepcopy((target, patch))
        result = r.json_merge_patch(target, patch)
        self.assertEqual(result, {"title": "New", "author": {"name": "Ada"}, "tags": [2]})
        result["tags"].append(3)
        self.assertEqual((target, patch), before)

    def test_merge_patch_replaces_non_objects(self):
        cases = [(1, {"a": 2}, {"a": 2}), ({"a": 1}, None, None),
                 ({"a": 1}, [2], [2]), ([1], {"a": None}, {}),
                 ({}, {"a": {"b": None}}, {"a": {}})]
        for target, patch, expected in cases:
            with self.subTest(patch=patch):
                self.assertEqual(r.json_merge_patch(target, patch), expected)

    def test_project_nested_fields_defaults_and_independence(self):
        records = [{"name": "Tea", "prices": [3], "stock": None}, {"name": "Coffee"}]
        result = r.json_project(iter(records), {"label": "/name", "cost": "/prices/0", "stock": "/stock"}, default="n/a")
        self.assertEqual(result, [{"label": "Tea", "cost": 3, "stock": None},
                                  {"label": "Coffee", "cost": "n/a", "stock": "n/a"}])
        copied = r.json_project(records, {"prices": "/prices"}, default=[])
        copied[0]["prices"].append(7)
        self.assertEqual(records[0]["prices"], [3])

    def test_project_validates_empty_inputs(self):
        self.assertEqual(r.json_project([], {"name": "/name"}), [])
        with self.assertRaises(ValueError):
            r.json_project([], {"name": "invalid"})
        with self.assertRaises(TypeError):
            r.json_project([1], {"name": "/name"})
        with self.assertRaises(TypeError):
            r.json_project([], {1: "/name"})


class JsonLinesTests(unittest.TestCase):
    def test_read_strings_and_streams_lazily(self):
        source = '{"name":"Té"}\r\nnull\n[1,2]\n'
        expected = [{"name": "Té"}, None, [1, 2]]
        self.assertEqual(list(r.iter_jsonl(source)), expected)
        self.assertEqual(list(r.iter_jsonl(io.StringIO(source))), expected)
        stream = io.StringIO('1\nnot-json\n')
        records = r.iter_jsonl(stream)
        self.assertEqual(next(records), 1)
        with self.assertRaisesRegex(ValueError, "line 2") as raised:
            next(records)
        self.assertNotIn("not-json", str(raised.exception))
        self.assertFalse(stream.closed)

    def test_blank_line_policy(self):
        self.assertEqual(list(r.iter_jsonl("")), [])
        with self.assertRaisesRegex(ValueError, "line 2"):
            list(r.iter_jsonl("1\n\n2"))
        self.assertEqual(list(r.iter_jsonl("\n1\n \n2", skip_blank=True)), [1, 2])

    def test_nonfinite_and_bom_rejected_without_payload_leak(self):
        for source in ['NaN', 'Infinity', '1e400', '\ufeff{}', '{"x":NaN}']:
            with self.subTest(source=source), self.assertRaises(ValueError):
                list(r.iter_jsonl(source))
        with self.assertRaises(TypeError):
            list(r.iter_jsonl([b"{}\n"]))

    def test_dump_round_trip_and_strict_json(self):
        data = [{"text": "two\nlines", "name": "Té"}, None, False, [1, 2]]
        result = r.jsonl_dumps(iter(data))
        self.assertEqual(len(result.splitlines()), 4)
        self.assertTrue(result.endswith("\n"))
        self.assertEqual(list(r.iter_jsonl(result)), data)
        self.assertEqual(r.jsonl_dumps([]), "")
        with self.assertRaises(ValueError):
            r.jsonl_dumps([float("nan")])

    def test_dump_rejects_lone_surrogates_in_values_and_keys(self):
        for record in ["\udcff", {"\ud800": "x"}, {"x": "\ud800"}]:
            with self.subTest(kind=type(record)), self.assertRaises(UnicodeError):
                r.jsonl_dumps([record])


class CsvTests(unittest.TestCase):
    def test_union_headers_and_round_trip(self):
        data = [{"name": "Tea, green", "price": 2, "note": 'a "quote"\nand newline'},
                {"name": "Coffee", "stock": True}]
        text = r.records_to_csv(iter(data))
        self.assertTrue(text.startswith("name,price,note,stock\r\n"))
        self.assertEqual(r.csv_to_records(text), [
            {"name": "Tea, green", "price": "2", "note": 'a "quote"\nand newline', "stock": ""},
            {"name": "Coffee", "price": "", "note": "", "stock": "true"},
        ])

    def test_explicit_columns_nested_json_and_null(self):
        text = r.records_to_csv([{"a": [1, 2], "b": None, "c": 3}], fieldnames=["b", "a"])
        self.assertEqual(r.csv_to_records(text), [{"b": "", "a": "[1,2]"}])
        self.assertEqual(r.records_to_csv([]), "")
        self.assertEqual(r.records_to_csv([], fieldnames=["a"]), "a\r\n")
        self.assertEqual(r.csv_to_records(""), [])
        self.assertEqual(r.csv_to_records("a,b\n"), [])

    def test_formula_prefixes_are_escaped_by_default_including_headers(self):
        dangerous = ["=1+1", "+cmd", "-cmd", "@SUM(A1)", "\t=1", "\r=1", " \t=1"]
        rows = [{"=field": value} for value in dangerous]
        decoded = r.csv_to_records(r.records_to_csv(rows))
        self.assertEqual([row["'=field"] for row in decoded], ["'" + s for s in dangerous])
        self.assertEqual(r.csv_to_records(r.records_to_csv(rows, escape_formulas=False)), rows)
        self.assertEqual(r.csv_to_records(r.records_to_csv([{"number": -2}])), [{"number": "-2"}])

    def test_delimiters_and_bom(self):
        text = r.records_to_csv([{"a": "x;y"}], delimiter=";")
        self.assertEqual(r.csv_to_records("\ufeff" + text, delimiter=";"), [{"a": "x;y"}])
        for delimiter in ["", "::", "\n", '"']:
            with self.subTest(delimiter=delimiter), self.assertRaises(ValueError):
                r.csv_to_records("a\nb", delimiter=delimiter)

    def test_leading_blank_rows_are_ignored_and_bare_quotes_are_literal(self):
        self.assertEqual(r.csv_to_records('\r\n\na\nb"c\n'), [{"a": 'b"c'}])
        self.assertEqual(r.csv_to_records('\r\n\n'), [])

    def test_fieldnames_reject_strings_and_escaped_collisions(self):
        for names in ["name", b"name"]:
            with self.subTest(names=names), self.assertRaises(TypeError):
                r.records_to_csv([], fieldnames=names)
        with self.assertRaises(ValueError):
            r.records_to_csv([], fieldnames=["=a", "'=a"])

    def test_malformed_records_and_headers_fail_explicitly(self):
        for source in ["a,a\n1,2", "a,b\n1", "a\n1,2", 'a\n"unclosed']:
            with self.subTest(source=source), self.assertRaises(ValueError):
                r.csv_to_records(source)
        for records in [[1], [{1: "value"}], [{"a": float("inf")}]]:
            with self.subTest(kind=type(records[0])), self.assertRaises((ValueError, TypeError)):
                r.records_to_csv(records)
        with self.assertRaises(ValueError):
            r.records_to_csv([], fieldnames=["a", "a"])


if __name__ == "__main__":
    unittest.main()
