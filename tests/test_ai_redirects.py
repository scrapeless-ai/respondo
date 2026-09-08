"""Authenticated provider requests must never follow redirects; no network I/O."""

from email.message import Message
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import urllib.request
import urllib.response

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import ai


class RedirectTests(unittest.TestCase):
    def test_authenticated_redirect_is_rejected_before_second_request(self):
        for code in (301, 302, 303, 307, 308):
            for target in ("https://other.example.test/", "http://other.example.test/", "https://api.openai.com/moved"):
                seen = []

                class FakeTransport(urllib.request.BaseHandler):
                    handler_order = 0

                    def default_open(self, request):
                        seen.append(request)
                        headers = Message()
                        headers["Location"] = target
                        response = urllib.response.addinfourl(io.BytesIO(b""), headers, request.full_url, code)
                        response.msg = "Synthetic redirect"
                        return response

                real_builder = urllib.request.build_opener

                def build(*handlers):
                    return real_builder(FakeTransport(), *handlers)

                with self.subTest(code=code, target=target), patch.object(ai.urllib.request, "build_opener", side_effect=build):
                    # Keep the test offline even before the safe opener exists.
                    with patch.object(ai.urllib.request, "urlopen", side_effect=AssertionError("unsafe default transport")):
                        with self.assertRaises(ai.AIError) as caught:
                            ai.parse("x", "y", model="example-model", api_key="synthetic", strict=True)
                    self.assertEqual(caught.exception.code, "http_error")
                    self.assertEqual(caught.exception.status_code, code)
                    self.assertEqual(len(seen), 1)
                    self.assertIsNone(caught.exception.__context__)


if __name__ == "__main__":
    unittest.main()
