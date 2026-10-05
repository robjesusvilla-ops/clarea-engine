import json
import unittest
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from clarea.connectors.meta_graph import MetaGraphClient, MetaGraphError


class FakeGraph:
    """Answers Graph API URLs with canned data and records every request."""

    def __init__(self, broken_metrics=()):
        self.calls = []
        self.broken = set(broken_metrics)

    def __call__(self, url, headers):
        self.calls.append((url, headers))
        parsed = urllib.parse.urlparse(url)
        path = parsed.path.split("/", 2)[2]  # drop the API version
        q = dict(urllib.parse.parse_qsl(parsed.query))
        if path == "123":
            return {"name": "Qhatai Piscinas", "followers_count": 5000}
        if path == "123/published_posts":
            if q.get("after") == "page2":
                return {"data": [self._post("p2", "Oferta: 10% de descuento", "photo", 5, 0, 0)]}
            return {"data": [self._post("p1", "Proyecto terminado en La Molina", "album", 120, 10, 4)],
                    "paging": {"next": "https://graph.facebook.com/v21.0/123/published_posts?after=page2"}}
        if path.endswith("/insights"):
            metric = q["metric"]
            if metric in self.broken:
                return {"error": {"message": "metric retired"}}
            value = {"post_impressions_unique": 1000, "post_impressions": 1300, "post_clicks": 40,
                     "page_messages_new_conversations_unique": 7, "page_daily_follows_unique": 3}[metric]
            return {"data": [{"name": metric, "values": [{"value": value}, {"value": value if path == "123/insights" else 0}]}]}
        raise AssertionError(f"unexpected url {url}")

    @staticmethod
    def _post(pid, message, media, likes, comments, shares):
        return {"id": pid, "message": message, "created_time": "2026-05-04T10:00:00+0000",
                "attachments": {"data": [{"media_type": media}]},
                "reactions": {"summary": {"total_count": likes}},
                "comments": {"summary": {"total_count": comments}},
                "shares": {"count": shares}}


class TestMetaGraph(unittest.TestCase):
    def fetch(self, fake):
        client = MetaGraphClient(token="SECRET-TOKEN", http_get=fake)
        return client.fetch_period("123", "2026-05-01", "2026-05-31", "Mayo 2026", industry="piscinas")

    def test_builds_period_from_api(self):
        s = self.fetch(FakeGraph())
        self.assertEqual(s.brand_name, "Qhatai Piscinas")
        self.assertEqual(s.posts_count, 2)  # followed pagination
        p1 = s.posts[0]
        self.assertEqual((p1.reach, p1.impressions, p1.clicks), (1000, 1300, 40))
        self.assertEqual(p1.content_type, "carousel")
        self.assertEqual(p1.interactions, 134)
        self.assertEqual(p1.topic, "Resultados / Proyectos")
        self.assertEqual(s.posts[1].topic, "Promoción / Venta")
        # Page-level totals summed over the daily values.
        self.assertEqual(s.total_messages, 14)
        self.assertEqual(s.new_followers, 6)

    def test_token_only_travels_in_header(self):
        fake = FakeGraph()
        self.fetch(fake)
        for url, headers in fake.calls:
            self.assertNotIn("SECRET-TOKEN", url)
            self.assertEqual(headers["Authorization"], "Bearer SECRET-TOKEN")

    def test_retired_metric_does_not_break_fetch(self):
        s = self.fetch(FakeGraph(broken_metrics={"post_clicks", "page_messages_new_conversations_unique"}))
        self.assertEqual(s.posts[0].clicks, 0)
        self.assertEqual(s.total_messages, 0)
        self.assertEqual(s.posts[0].reach, 1000)

    def test_missing_token_is_explained(self):
        import os
        old = os.environ.pop("META_PAGE_TOKEN", None)
        try:
            with self.assertRaises(MetaGraphError) as ctx:
                MetaGraphClient(http_get=FakeGraph())
            self.assertIn("META_PAGE_TOKEN", str(ctx.exception))
        finally:
            if old is not None:
                os.environ["META_PAGE_TOKEN"] = old

    def test_output_is_valid_analyze_input(self):
        from clarea.core.parser import MetricParser
        s = self.fetch(FakeGraph())
        again = MetricParser.from_dict(json.loads(s.model_dump_json()))
        self.assertEqual(again.posts_count, 2)


if __name__ == "__main__":
    unittest.main()
