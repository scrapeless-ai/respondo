"""Legacy AI adapter contracts: all transport and key lookup use synthetic mocks."""

from contextlib import nullcontext
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import ai


class AiContractTests(unittest.TestCase):
    def test_each_adapter_constructs_local_request_and_keeps_key_out_of_url(self):
        for provider, config in ai.PROVIDERS.items():
            for schema in (None, {"type": "object"}):
                with self.subTest(provider=provider, schema=schema), patch.object(ai, "_http_post", return_value="ok") as post:
                    self.assertEqual(config["handler"]("extract", "synthetic content", "example-only-not-a-credential", "example-model", schema), "ok")
                    url, headers, payload, response_path = post.call_args.args
                    self.assertTrue(url.startswith("https://"))
                    self.assertNotIn("example-only-not-a-credential", url)
                    self.assertTrue(any("example-only-not-a-credential" in value for value in headers.values()))
                    self.assertIn("synthetic content", json.dumps(payload))
                    self.assertIn("example-model", url + json.dumps(payload))
                    self.assertTrue(response_path)

    def test_transport_extracts_response_and_uses_json_post(self):
        response = {"choices": [{"message": {"content": "answer"}}]}
        with patch.object(ai, "_open_request", return_value=nullcontext(io.BytesIO(json.dumps(response).encode()))) as request:
            result = ai._http_post("https://example.test/api", {"Content-Type": "application/json"}, {"prompt": "synthetic"}, ["choices", 0, "message", "content"])
        self.assertEqual(result, "answer")
        self.assertEqual(request.call_args.args[0].method, "POST")
        self.assertEqual(json.loads(request.call_args.args[0].data), {"prompt": "synthetic"})
        self.assertEqual(request.call_args.kwargs["timeout"], 120)

    def test_transport_returns_legacy_empty_result_for_invalid_responses(self):
        for response, path in [({}, ["missing"]), ({"items": []}, ["items", 0]), ({"items": {}}, ["items", 0]),
                               ({"items": [0]}, ["items", 0]), ({"items": [1]}, ["items", "key"])]:
            with self.subTest(response=response), patch.object(ai, "_open_request", return_value=nullcontext(io.BytesIO(json.dumps(response).encode()))):
                self.assertEqual(ai._http_post("https://example.test/", {}, {}, path), "")
        with patch.object(ai, "_open_request", side_effect=OSError("synthetic failure")):
            self.assertEqual(ai._http_post("https://example.test/", {}, {}, []), "")
        with patch.object(ai, "_open_request", return_value=nullcontext(io.BytesIO(b"not JSON"))):
            self.assertEqual(ai._http_post("https://example.test/", {}, {}, []), "")

    def test_environment_key_mapping_uses_only_mock_values(self):
        with patch.object(ai.os.environ, "get", return_value="synthetic") as lookup:
            self.assertEqual(ai._get_api_key("gemini"), "synthetic")
            lookup.assert_called_once_with("GEMINI_API_KEY", "")
        with patch.object(ai.os.environ, "get", return_value=""):
            self.assertEqual(ai._get_api_key("unknown"), "")

    def test_empty_inputs_missing_key_and_unknown_provider_do_not_call_transport(self):
        with patch.object(ai, "_get_api_key", return_value=""), patch.object(ai, "_http_post") as post:
            for prompt, content in [("", "x"), ("x", ""), ("x", "y")]:
                self.assertEqual(ai.parse(prompt, content), "")
                self.assertIsNone(ai.parse_json(prompt, content))
            self.assertEqual(ai.parse("x", "y", provider="unknown", api_key="synthetic"), "")
            self.assertIsNone(ai.parse_json("x", "y", provider="unknown", api_key="synthetic"))
            post.assert_not_called()

    def test_parse_selects_explicit_model(self):
        for provider, config in ai.PROVIDERS.items():
            with self.subTest(provider=provider), patch.object(ai, "_http_post", return_value="answer") as post:
                self.assertEqual(ai.parse("extract", "text", provider=provider, model="custom-model", api_key="synthetic"), "answer")
                self.assertIn("custom-model", post.call_args.args[0] + json.dumps(post.call_args.args[2]))

    def test_json_outputs_code_fences_schema_and_invalid_results(self):
        for raw, expected in [(' {"ok": true} ', {"ok": True}), ('```json\n{"ok": true}\n```', {"ok": True}),
                              ('```json\n[1,2]', [1, 2]), ("", None), ("not JSON", None), ("```", None)]:
            with self.subTest(raw=raw), patch.object(ai, "_http_post", return_value=raw):
                self.assertEqual(ai.parse_json("extract", "synthetic", model="example-model", api_key="synthetic"), expected)
        with patch.object(ai, "_http_post", return_value='{"ok": true}') as post:
            self.assertEqual(ai.parse_json("extract", "synthetic", model="example-model", api_key="synthetic", schema={"type": "object"}), {"ok": True})
            self.assertEqual(post.call_args.args[2]["response_format"]["json_schema"]["schema"], {"type": "object"})

    def test_provider_listing_is_an_independent_mapping(self):
        providers = ai.list_providers()
        self.assertEqual(set(providers), set(ai.PROVIDERS))
        providers["openai"] = "changed"
        self.assertNotEqual(ai.list_providers()["openai"], "changed")


if __name__ == "__main__":
    unittest.main()
