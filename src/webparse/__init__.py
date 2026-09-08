"""Dependency-free URL, feed and sitemap extraction; no network requests."""

from .feeds import parse_feed, parse_sitemap
from .urls import normalize_url, update_url_query

__all__ = ["normalize_url", "update_url_query", "parse_feed", "parse_sitemap"]
