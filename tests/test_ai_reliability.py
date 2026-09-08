"""AI configuration, schema and sanitized failure contracts; no live requests."""

from contextlib import nullcontext
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import ai


class AiReliabilityTests(unittest.TestCase):
    def test_environment_models_and_explicit_precedence_for_every_provider(self):
        for provider in ai.PROVIDERS:
            for parse in (ai.parse, ai.parse_json):
                with self.subTest(provider=provider, parse=parse.__name__), patch.object(ai.os, "environ", {provider.upper() + "_MODEL": " configured-model "}), patch.object(ai, "_http_post", return_value='{"ok":true}') as post:
                    parse("extract", "synthetic", provider=provider, api_key="synthetic")
                    self.assertIn("configured-model", post.call_args.args[0] + json.dumps(post.call_args.args[2]))
                    parse("extract", "synthetic", provider=provider, model="chosen-model", api_key="synthetic")
                    self.assertIn("chosen-model", post.call_args.args[0] + json.dumps(post.call_args.args[2]))

    def test_missing_or_invalid_model_never_calls_transport(self):
        for value in (None, "", "  ", 123):
            with self.subTest(value=value), patch.object(ai.os, "environ", {}), patch.object(ai, "_http_post") as post:
                self.assertEqual(ai.parse("x", "y", model=value, api_key="synthetic"), "")
                self.assertIsNone(ai.parse_json("x", "y", model=value, api_key="synthetic"))
                post.assert_not_called()

    def test_provider_listing_reports_variable_names_not_models(self):
        self.assertEqual(ai.list_providers(), {p: p.upper() + "_MODEL" for p in ai.PROVIDERS})
        self.assertTrue(all("default_model" not in config for config in ai.PROVIDERS.values()))

    def test_every_adapter_receives_schema_in_request(self):
        schema = {"type": "object", "properties": {"unique_contract_field": {"type": "integer"}}, "required": ["unique_contract_field"]}
        for provider, config in ai.PROVIDERS.items():
            with self.subTest(provider=provider), patch.object(ai, "_http_post", return_value="ok") as post:
                config["handler"]("extract", "synthetic", "synthetic", "example-model", schema)
                self.assertIn("unique_contract_field", json.dumps(post.call_args.args[2]))

    def test_empty_schema_is_forwarded_by_every_adapter(self):
        for provider, config in ai.PROVIDERS.items():
            with self.subTest(provider=provider), patch.object(ai, "_http_post", return_value="ok") as post:
                config["handler"]("extract", "synthetic", "synthetic", "example-model", {})
                self.assertIn("schema", json.dumps(post.call_args.args[2]).lower())

    def test_strict_configuration_failures_are_actionable(self):
        cases = [({"provider": "unknown"}, "unknown_provider"), ({}, "missing_model"),
                 ({"model": "example-model"}, "missing_api_key"), ({"model": 3}, "invalid_model")]
        with patch.object(ai.os, "environ", {}), patch.object(ai, "_http_post") as post:
            for kwargs, code in cases:
                for parse in (ai.parse, ai.parse_json):
                    with self.subTest(kwargs=kwargs, parse=parse.__name__), self.assertRaises(ai.AIError) as caught:
                        parse("x", "y", strict=True, **kwargs)
                    self.assertEqual(caught.exception.code, code)
            post.assert_not_called()

    def test_strict_transport_errors_are_sanitized_without_exception_context(self):
        marker = "SYNTHETIC_PRIVATE_BODY"
        cases = [(HTTPError("https://example.test/" + marker, 401, marker, {}, io.BytesIO(marker.encode())), "authentication", 401),
                 (HTTPError("https://example.test/", 429, marker, {}, None), "rate_limit", 429),
                 (HTTPError("https://example.test/", 503, marker, {}, None), "http_error", 503),
                 (TimeoutError(marker), "timeout", None),
                 (URLError(TimeoutError(marker)), "timeout", None),
                 (URLError(marker), "connection", None), (OSError(marker), "connection", None)]
        for error, code, status in cases:
            with self.subTest(code=code), patch.object(ai, "_open_request", side_effect=error):
                with self.assertRaises(ai.AIError) as caught:
                    ai.parse("extract", "synthetic", model="example-model", api_key="synthetic", strict=True)
                self.assertEqual(caught.exception.code, code)
                self.assertEqual(caught.exception.status_code, status)
                self.assertNotIn(marker, str(caught.exception))
                self.assertIsNone(caught.exception.__context__)
                self.assertEqual(ai.parse("extract", "synthetic", model="example-model", api_key="synthetic"), "")

    def test_strict_invalid_response_and_json(self):
        for data in (b"not-json", b"{}", b'{"choices":[]}'):
            with self.subTest(data=data), patch.object(ai, "_open_request", return_value=nullcontext(io.BytesIO(data))):
                with self.assertRaises(ai.AIError) as caught:
                    ai.parse("x", "y", model="example-model", api_key="synthetic", strict=True)
                self.assertEqual(caught.exception.code, "invalid_response")
        for data in ("not-json", "NaN", '{"x":Infinity}', "1e9999", '{"x":1e9999}'):
            with self.subTest(data=data), patch.object(ai, "_http_post", return_value=data):
                with self.assertRaises(ai.AIError) as caught:
                    ai.parse_json("x", "y", model="example-model", api_key="synthetic", strict=True)
                self.assertEqual(caught.exception.code, "invalid_json")

    def test_invalid_unicode_model_and_http_cleanup_stay_sanitized(self):
        for provider in ai.PROVIDERS:
            with self.subTest(provider=provider), patch.object(ai, "_http_post") as post:
                self.assertEqual(ai.parse("x", "y", provider=provider, model="bad\ud800", api_key="synthetic"), "")
                with self.assertRaises(ai.AIError) as caught:
                    ai.parse("x", "y", provider=provider, model="bad\ud800", api_key="synthetic", strict=True)
                self.assertEqual(caught.exception.code, "invalid_model")
                self.assertIsNone(caught.exception.__context__)
                post.assert_not_called()
        error = HTTPError("https://example.test", 401, "synthetic", {}, None)
        with patch.object(error, "close", side_effect=OSError("SYNTHETIC_PRIVATE")), patch.object(ai, "_open_request", side_effect=error):
            with self.assertRaises(ai.AIError) as caught:
                ai.parse("x", "y", model="example-model", api_key="synthetic", strict=True)
            self.assertEqual(caught.exception.code, "authentication")
            self.assertIsNone(caught.exception.__context__)
            self.assertEqual(ai.parse("x", "y", model="example-model", api_key="synthetic"), "")

    def test_public_error_export_and_json_success(self):
        from respondo import AIError
        self.assertIs(AIError, ai.AIError)
        with patch.object(ai, "_http_post", return_value='```json\n{"ok":true}\n```'):
            self.assertEqual(ai.parse_json("x", "y", model="example-model", api_key="synthetic", strict=True), {"ok": True})


if __name__ == "__main__":
    unittest.main()
