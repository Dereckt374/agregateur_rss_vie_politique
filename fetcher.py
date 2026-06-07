import html
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

import feedparser

logger = logging.getLogger(__name__)

RSS_FEEDS: dict[str, str] = {
    "Assemblée Nationale – Communiqués de presse": (
        "https://www.assemblee-nationale.fr/rss/communiques-de-presse.xml"
    ),
    "Assemblée Nationale – Comptes-rendus des débats": (
        "http://www2.assemblee-nationale.fr/feeds/detail/crs"
    ),
    "Assemblée Nationale – Commission des Finances": (
        "http://www2.assemblee-nationale.fr/feeds/detail/ID_59048/(type)/instance"
    ),
    "Assemblée Nationale – Commission des Lois": (
        "http://www2.assemblee-nationale.fr/feeds/detail/ID_59051/(type)/instance"
    ),
    "Assemblée Nationale – Commission des Affaires sociales": (
        "http://www2.assemblee-nationale.fr/feeds/detail/ID_420120/(type)/instance"
    ),
    "Sénat – Communiqués de presse": "https://www.senat.fr/rss/presse.rss",
    "Sénat – Textes législatifs": "https://www.senat.fr/rss/textes.rss",
    "Sénat – Rapports": "https://www.senat.fr/rss/rapports.rss",
}

_HTML_TAG = re.compile(r"<[^>]+>")
_WHITESPACE = re.compile(r"\s+")


@dataclass
class FeedItem:
    source: str
    title: str
    summary: str
    link: str
    published: Optional[datetime]


def _clean_html(text: str) -> str:
    text = _HTML_TAG.sub(" ", text)
    text = html.unescape(text)
    return _WHITESPACE.sub(" ", text).strip()


def _parse_date(entry) -> Optional[datetime]:
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc)
            except (ValueError, TypeError):
                pass
    return None


def fetch_items(days: int = 7) -> list[FeedItem]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    items: list[FeedItem] = []

    for source, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            if feed.bozo and not feed.entries:
                logger.warning("Flux inaccessible ou invalide : %s", source)
                continue
            for entry in feed.entries:
                published = _parse_date(entry)
                if published and published < cutoff:
                    continue
                raw_summary = (
                    getattr(entry, "summary", "")
                    or getattr(entry, "description", "")
                    or ""
                )
                summary = _clean_html(raw_summary)[:400]
                items.append(
                    FeedItem(
                        source=source,
                        title=_clean_html(entry.get("title", "Sans titre")),
                        summary=summary,
                        link=entry.get("link", ""),
                        published=published,
                    )
                )
        except Exception:
            logger.exception("Erreur lors de la récupération du flux : %s", source)

    items.sort(
        key=lambda x: x.published or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    return items


def format_for_prompt(items: list[FeedItem], max_items: int = 60) -> str:
    lines: list[str] = []
    for item in items[:max_items]:
        date_str = item.published.strftime("%d/%m/%Y") if item.published else "date inconnue"
        lines.append(f"[{item.source}] {date_str} — {item.title}")
        if item.summary:
            lines.append(f"  {item.summary}")
        lines.append("")
    return "\n".join(lines)
