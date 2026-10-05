"""Read-only connector for Facebook Page data through the Meta Graph API.

Security:
- The page token is read from the META_PAGE_TOKEN environment variable and
  sent in the Authorization header, so it never appears in URLs, files or logs.
- Only read permissions are needed: pages_read_engagement and read_insights.

Known limits of the Graph API (not of Clarea):
- Messages cannot be attributed to individual posts. The page-level count of
  new conversations is used as the period total when Meta returns it.
- Meta renames and retires insight metrics between API versions. Every
  insight request here is tolerant: a missing metric becomes 0 instead of
  breaking the whole fetch.
"""
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable, Dict, Iterator, List, Optional

from clarea.core.classifier import infer_angle
from clarea.core.models import PeriodSummary, PostMetric
from clarea.core.parser import UNCLASSIFIED_TOPIC, MetricParser

GRAPH_URL = "https://graph.facebook.com"
DEFAULT_API_VERSION = "v21.0"
TOKEN_ENV = "META_PAGE_TOKEN"
PAGE_ID_ENV = "META_PAGE_ID"

POST_FIELDS = ("id,message,created_time,attachments{media_type},shares,"
               "comments.summary(true).limit(0),reactions.summary(true).limit(0)")
POST_REACH_METRIC = "post_impressions_unique"
POST_IMPRESSIONS_METRIC = "post_impressions"
POST_CLICKS_METRIC = "post_clicks"
PAGE_MESSAGES_METRIC = "page_messages_new_conversations_unique"
PAGE_NEW_FOLLOWERS_METRIC = "page_daily_follows_unique"

MEDIA_TYPES = {"photo": "photo", "album": "carousel", "video": "video", "video_inline": "video",
               "reel": "reel", "share": "text", "link": "text", "status": "text"}

HttpGet = Callable[[str, Dict[str, str]], Dict[str, Any]]


class MetaGraphError(RuntimeError):
    pass


def _urllib_get(url: str, headers: Dict[str, str]) -> Dict[str, Any]:
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            detail = json.loads(e.read().decode("utf-8")).get("error", {}).get("message", "")
        except Exception:
            detail = ""
        raise MetaGraphError(f"Meta respondió {e.code}: {detail or e.reason}") from None
    except urllib.error.URLError as e:
        raise MetaGraphError(f"No se pudo conectar con Meta: {e.reason}") from None


class MetaGraphClient:

    def __init__(self, token: Optional[str] = None, api_version: str = DEFAULT_API_VERSION,
                 http_get: Optional[HttpGet] = None):
        self.token = token or os.environ.get(TOKEN_ENV)
        if not self.token:
            raise MetaGraphError(
                f"Falta el token de página. Guárdalo en la variable de entorno {TOKEN_ENV} "
                "(nunca dentro del código ni en GitHub)."
            )
        self.base = f"{GRAPH_URL}/{api_version}"
        self._get = http_get or _urllib_get

    def _request(self, path_or_url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = path_or_url if path_or_url.startswith("http") else f"{self.base}/{path_or_url.lstrip('/')}"
        if params:
            url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
        data = self._get(url, {"Authorization": f"Bearer {self.token}"})
        if isinstance(data, dict) and "error" in data:
            raise MetaGraphError(f"Meta respondió con error: {data['error'].get('message', 'desconocido')}")
        return data

    def _paginate(self, path: str, params: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
        data = self._request(path, params)
        while True:
            yield from data.get("data", [])
            next_url = data.get("paging", {}).get("next")
            if not next_url:
                return
            data = self._request(next_url)

    def page_info(self, page_id: str) -> Dict[str, Any]:
        return self._request(page_id, {"fields": "name,followers_count,fan_count"})

    def published_posts(self, page_id: str, since: str, until: str) -> List[Dict[str, Any]]:
        return list(self._paginate(f"{page_id}/published_posts",
                                   {"fields": POST_FIELDS, "since": since, "until": until, "limit": 100}))

    def insights(self, object_id: str, metrics: List[str], **params) -> Dict[str, int]:
        """Returns {metric: value}; metrics Meta rejects are reported as 0."""
        values: Dict[str, int] = {}
        for metric in metrics:
            try:
                data = self._request(f"{object_id}/insights", {"metric": metric, **params})
            except MetaGraphError:
                values[metric] = 0
                continue
            total = 0
            for entry in data.get("data", []):
                for point in entry.get("values", []):
                    v = point.get("value", 0)
                    total += v if isinstance(v, int) else 0
            values[metric] = total
        return values

    def fetch_period(self, page_id: Optional[str], since: str, until: str, period_label: str,
                     brand_name: Optional[str] = None, industry: Optional[str] = None) -> PeriodSummary:
        page_id = page_id or os.environ.get(PAGE_ID_ENV)
        if not page_id:
            raise MetaGraphError(f"Falta el ID de la página. Indícalo o guárdalo en {PAGE_ID_ENV}.")
        info = self.page_info(page_id)
        posts = [self._to_post(raw) for raw in self.published_posts(page_id, since, until)]
        page = self.insights(page_id, [PAGE_MESSAGES_METRIC, PAGE_NEW_FOLLOWERS_METRIC],
                             period="day", since=since, until=until)
        summary = MetricParser.summary_from_posts(
            posts, brand_name or info.get("name", "Mi página"), period_label, industry,
            new_followers=page.get(PAGE_NEW_FOLLOWERS_METRIC, 0),
        )
        summary.total_messages = page.get(PAGE_MESSAGES_METRIC, 0)
        return summary

    def _to_post(self, raw: Dict[str, Any]) -> PostMetric:
        ins = self.insights(raw["id"], [POST_REACH_METRIC, POST_IMPRESSIONS_METRIC, POST_CLICKS_METRIC],
                            period="lifetime")
        likes = raw.get("reactions", {}).get("summary", {}).get("total_count", 0)
        comments = raw.get("comments", {}).get("summary", {}).get("total_count", 0)
        shares = raw.get("shares", {}).get("count", 0)
        attachments = raw.get("attachments", {}).get("data", [])
        media = attachments[0].get("media_type", "status") if attachments else "status"
        message = (raw.get("message") or "").strip()
        reach = ins[POST_REACH_METRIC]
        return PostMetric(
            id=raw["id"],
            content_type=MEDIA_TYPES.get(media, "photo"),
            topic=infer_angle(message) or UNCLASSIFIED_TOPIC,
            reach=reach,
            impressions=ins[POST_IMPRESSIONS_METRIC] or reach,
            interactions=likes + comments + shares,
            likes=likes,
            comments=comments,
            shares=shares,
            clicks=ins[POST_CLICKS_METRIC],
            published_date=(raw.get("created_time") or "")[:10] or None,
            caption_preview=message[:160] or None,
        )
