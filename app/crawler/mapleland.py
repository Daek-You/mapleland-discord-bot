"""Crawler for Mapleland notice pages."""

from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.config import (
    DEFAULT_MAPLELAND_REQUEST_TIMEOUT_SECONDS,
    MAPLELAND_NOTICE_LIST_URL,
    MAPLELAND_NOTICE_PATH_PREFIX,
)


class MaplelandCrawlerError(RuntimeError):
    """Raised when Mapleland notice crawling fails."""


@dataclass(frozen=True)
class NoticeItem:
    """A Mapleland notice list item."""

    title: str
    url: str


def fetch_latest_notice_items(
    notice_list_url: str = MAPLELAND_NOTICE_LIST_URL,
    client: httpx.Client | None = None,
) -> list[NoticeItem]:
    """Fetch latest Mapleland notice titles and URLs."""
    if client is None:
        with httpx.Client(
            timeout=DEFAULT_MAPLELAND_REQUEST_TIMEOUT_SECONDS
        ) as default_client:
            return _fetch_latest_notice_items_with_client(default_client, notice_list_url)

    return _fetch_latest_notice_items_with_client(client, notice_list_url)


def parse_notice_items(
    html: str,
    base_url: str = MAPLELAND_NOTICE_LIST_URL,
) -> list[NoticeItem]:
    """Parse Mapleland notice items from a notice list HTML document."""
    soup = BeautifulSoup(html, "html.parser")
    notice_items: list[NoticeItem] = []
    seen_urls: set[str] = set()

    for link in soup.find_all("a", href=True):
        href = str(link["href"])
        if not _is_notice_detail_href(href):
            continue

        title = _clean_notice_title(link.get_text(" ", strip=True))
        if not title:
            continue

        notice_url = urljoin(base_url, href)
        if notice_url in seen_urls:
            continue

        notice_items.append(NoticeItem(title=title, url=notice_url))
        seen_urls.add(notice_url)

    return notice_items


def _fetch_latest_notice_items_with_client(
    client: httpx.Client,
    notice_list_url: str,
) -> list[NoticeItem]:
    try:
        response = client.get(notice_list_url)
        response.raise_for_status()
    except httpx.HTTPStatusError as error:
        raise MaplelandCrawlerError("Mapleland notice page returned an HTTP error.") from error
    except httpx.RequestError as error:
        raise MaplelandCrawlerError("Failed to request Mapleland notice page.") from error

    return parse_notice_items(response.text, base_url=notice_list_url)


def _is_notice_detail_href(href: str) -> bool:
    parsed_href = urlparse(href)
    return parsed_href.path.startswith(MAPLELAND_NOTICE_PATH_PREFIX) and (
        parsed_href.path != MAPLELAND_NOTICE_LIST_URL
    )


def _clean_notice_title(title: str) -> str:
    if title.endswith("N"):
        return title[:-1].strip()
    return title.strip()
