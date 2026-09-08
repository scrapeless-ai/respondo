"""URL and feed/sitemap contracts, using synthetic local inputs only."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import respondo as r


class UrlTests(unittest.TestCase):
    def test_normalize_only_conservative_components_by_default(self):
        self.assertEqual(r.normalize_url("HTTPS://EXAMPLE.TEST:443/A%2Fb?b=2&a=1#top"),
                         "https://example.test/A%2Fb?b=2&a=1#top")
        self.assertEqual(r.normalize_url("http://example.test:80"), "http://example.test/")
        self.assertEqual(r.normalize_url("https://bücher.test/"), "https://xn--bcher-kva.test/")
        self.assertEqual(r.normalize_url("https://[2001:DB8::1]:443/a"), "https://[2001:db8::1]/a")

    def test_base_and_explicit_query_cleanup(self):
        self.assertEqual(r.normalize_url("../item", base="https://example.test/a/b"), "https://example.test/item")
        source = "https://example.test/?z=&utm_source=x&a=2&a=1&fbclid=x#part"
        self.assertEqual(r.normalize_url(source, remove_tracking=True, sort_query=True, drop_fragment=True),
                         "https://example.test/?a=1&a=2&z=")

    def test_invalid_urls_are_rejected_without_echo(self):
        for url in ["/relative", "ftp://example.test/a", "https:///a", "https://example.test:bad/",
                    "https://u:p@example.test/", "https://example.test/a\nb", " https://example.test/",
                    "https://example.test\\evil", "https://[invalid]/", "https://example.test:99999/"]:
            with self.subTest(url=url), self.assertRaises(ValueError) as raised:
                r.normalize_url(url)
            self.assertNotIn(url, str(raised.exception))

    def test_update_duplicates_lists_removals_and_fragment(self):
        url = "https://example.test/a?k=old&x=1&k=again&empty=&x=2#anchor"
        result = r.update_url_query(url, {"k": ["new", "two words"], "empty": None, "page": 2})
        self.assertEqual(result, "https://example.test/a?x=1&x=2&k=new&k=two+words&page=2#anchor")
        self.assertEqual(r.update_url_query(result, {"k": [], "page": None}),
                         "https://example.test/a?x=1&x=2#anchor")

    def test_update_validates_inputs_and_handles_unicode(self):
        self.assertEqual(r.update_url_query("https://example.test/", {"q": "té", "flag": True}),
                         "https://example.test/?q=t%C3%A9&flag=true")
        for updates in [{1: "x"}, {"x": {}}, {"x": [None]}, {"x": float("inf")}, []]:
            with self.subTest(updates=updates), self.assertRaises((ValueError, TypeError)):
                r.update_url_query("https://example.test/", updates)

    def test_invalid_encoded_queries_fail_instead_of_losing_bytes(self):
        url = "https://example.test/?opaque=%FF&k=old"
        with self.assertRaises(ValueError):
            r.update_url_query(url, {"k": "new"})
        with self.assertRaises(ValueError):
            r.normalize_url(url, remove_tracking=True)
        self.assertEqual(r.normalize_url(url), url)

    def test_idna_output_and_bracket_identity_are_validated(self):
        for url in ["https://exa\u00a0mple.test/", "https://[v1.host]/", "https://[::1]extra/", "https://%65xample.test/"]:
            with self.subTest(url=url), self.assertRaises(ValueError):
                r.normalize_url(url)


class SitemapTests(unittest.TestCase):
    def test_urlset_with_namespaces_metadata_and_order(self):
        xml = '''<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <url><loc>https://example.test/a?x=1&amp;y=2</loc><lastmod>2026-01-01</lastmod>
        <changefreq>weekly</changefreq><priority>0.8</priority></url>
        <url><loc>https://example.test/b</loc></url></urlset>'''
        self.assertEqual(r.parse_sitemap(xml), {"type": "urlset", "entries": [
            {"loc": "https://example.test/a?x=1&y=2", "lastmod": "2026-01-01", "changefreq": "weekly", "priority": "0.8"},
            {"loc": "https://example.test/b", "lastmod": "", "changefreq": "", "priority": ""}]})

    def test_indexes_relative_urls_and_empty_shape(self):
        result = r.parse_sitemap('<sitemapindex><sitemap><loc>part.xml</loc></sitemap></sitemapindex>',
                                 base="https://example.test/maps/index.xml")
        self.assertEqual(result, {"type": "sitemapindex", "entries": [{"loc": "https://example.test/maps/part.xml", "lastmod": ""}]})
        self.assertEqual(r.parse_sitemap("<urlset/>"), {"type": "urlset", "entries": []})

    def test_missing_locations_and_wrong_roots_fail(self):
        for xml in ["<html/>", "<urlset><url/></urlset>", '<urlset xmlns="urn:foreign"/>']:
            with self.subTest(xml=xml), self.assertRaises(ValueError):
                r.parse_sitemap(xml)


class FeedTests(unittest.TestCase):
    def test_rss_metadata_entries_and_enclosures(self):
        xml = '''<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">
        <channel><title>Updates</title><link>https://example.test/</link><description>News</description><language>en</language>
        <item><guid isPermaLink="false">item-1</guid><title>Tea</title><link>/tea</link>
        <description><![CDATA[<p>Fresh & green</p>]]></description><content:encoded><![CDATA[<b>Full</b>]]></content:encoded>
        <pubDate>Mon, 07 Sep 2026 12:00:00 GMT</pubDate><author>Ada</author><category>Food</category>
        <enclosure url="/tea.mp3" type="audio/mpeg" length="123"/></item></channel></rss>'''
        feed = r.parse_feed(xml, base="https://example.test/feed.xml")
        self.assertEqual({k: v for k, v in feed.items() if k != "entries"},
                         {"format": "rss", "title": "Updates", "link": "https://example.test/", "description": "News", "language": "en"})
        self.assertEqual(feed["entries"], [{"id": "item-1", "title": "Tea", "link": "https://example.test/tea",
            "summary": "<p>Fresh & green</p>", "content": "<b>Full</b>", "published": "Mon, 07 Sep 2026 12:00:00 GMT",
            "updated": "", "authors": ["Ada"], "categories": ["Food"],
            "enclosures": [{"url": "https://example.test/tea.mp3", "type": "audio/mpeg", "length": "123"}]}])

    def test_atom_inherited_base_authors_and_alternate_link(self):
        xml = '''<feed xmlns="http://www.w3.org/2005/Atom" xml:base="https://example.test/" xml:lang="es">
        <title>Updates</title><subtitle>News</subtitle><link rel="self" href="feed.xml"/><link href="/"/>
        <author><name>Ada</name></author><entry xml:base="posts/"><id>urn:item:1</id><title>Uno</title>
        <link rel="self" href="1.xml"/><link href="1"/><link rel="enclosure" href="1.mp3" type="audio/mpeg" length="9"/>
        <summary type="html">&lt;p&gt;Hi&lt;/p&gt;</summary><published>2026-01-01T00:00:00Z</published>
        <updated>2026-01-02T00:00:00Z</updated><category term="news"/></entry></feed>'''
        feed = r.parse_feed(xml)
        self.assertEqual(feed["link"], "https://example.test/")
        self.assertEqual(feed["language"], "es")
        entry = feed["entries"][0]
        self.assertEqual(entry["link"], "https://example.test/posts/1")
        self.assertEqual(entry["enclosures"], [{"url": "https://example.test/posts/1.mp3", "type": "audio/mpeg", "length": "9"}])
        self.assertEqual(entry["authors"], ["Ada"])
        self.assertEqual(entry["categories"], ["news"])
        self.assertEqual(entry["summary"], "<p>Hi</p>")
        self.assertEqual(entry["updated"], "2026-01-02T00:00:00Z")

    def test_empty_feeds_entry_order_and_own_author(self):
        self.assertEqual(r.parse_feed("<rss><channel/></rss>")["entries"], [])
        xml = '<feed><author><name>Feed</name></author><entry><title>A</title><author><email>a@example.test</email></author></entry><entry><title>B</title></entry></feed>'
        entries = r.parse_feed(xml)["entries"]
        self.assertEqual([e["title"] for e in entries], ["A", "B"])
        self.assertEqual([e["authors"] for e in entries], [["a@example.test"], ["Feed"]])

    def test_unrecognized_feeds_and_malformed_xml_fail(self):
        for xml in ["<html/>", "<rss/>", "<feed>", '<feed xmlns="urn:foreign"/>']:
            with self.subTest(xml=xml), self.assertRaises(ValueError):
                r.parse_feed(xml)


class XmlSafetyTests(unittest.TestCase):
    def test_unknown_encoding_and_bad_base_have_controlled_errors(self):
        with self.assertRaisesRegex(ValueError, "encoding") as raised:
            r.parse_feed(b'<?xml version="1.0" encoding="X-UNSUPPORTED"?><feed/>')
        self.assertNotIn("X-UNSUPPORTED", str(raised.exception))
        for parser, xml in [(r.parse_feed, "<feed/>"), (r.parse_sitemap, "<urlset/>")]:
            with self.assertRaises(TypeError):
                parser(xml, base=0)

    def test_depth_and_base_expansion_have_explicit_limits(self):
        xml = "<feed><entry><content>" + "<div>" * 1200 + "x" + "</div>" * 1200 + "</content></entry></feed>"
        with self.assertRaisesRegex(ValueError, "depth"):
            r.parse_feed(xml)
        with self.assertRaisesRegex(ValueError, "base"):
            r.parse_feed('<feed xml:base="https://example.test/' + 'x' * 8192 + '"/>')

    def test_dtd_and_entities_rejected_even_in_utf16(self):
        for parser, root in [(r.parse_feed, "feed"), (r.parse_sitemap, "urlset")]:
            xml = '<!DOCTYPE ' + root + ' [<!ENTITY x "expanded">]><' + root + '>&x;</' + root + '>'
            for payload in [xml, xml.encode("utf-16")]:
                with self.subTest(parser=parser.__name__, kind=type(payload)), self.assertRaisesRegex(ValueError, "DTD"):
                    parser(payload)

    def test_size_limit_and_input_type(self):
        for parser, xml in [(r.parse_feed, "<feed/>"), (r.parse_sitemap, "<urlset/>")]:
            with self.assertRaisesRegex(ValueError, "limit"):
                parser(xml, max_bytes=2)
            with self.assertRaises(ValueError):
                parser(xml, max_bytes=0)
            with self.assertRaises(TypeError):
                parser(123)
            self.assertEqual(parser(xml.encode())["entries"], [])


if __name__ == "__main__":
    unittest.main()
