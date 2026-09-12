"""Crawler for Mapleland notice pages."""

from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.config import (
    DEFAULT_MAPLELAND_REQUEST_TIMEOUT_SECONDS,
    MAPLELAND_DEVLOG_LIST_URL,
    MAPLELAND_DEVLOG_PATH_PREFIX,
    MAPLELAND_EVENT_LIST_URL,
    MAPLELAND_EVENT_PATH_PREFIX,
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


async def fetch_latest_notice_items(
    notice_list_url: str = MAPLELAND_NOTICE_LIST_URL,
    client: httpx.AsyncClient | None = None,
) -> list[NoticeItem]:
    """Fetch latest Mapleland notice titles and URLs."""
    if client is None:
        async with httpx.AsyncClient(
            timeout=DEFAULT_MAPLELAND_REQUEST_TIMEOUT_SECONDS
        ) as default_client:
            return await _fetch_latest_notice_items_with_client(
                default_client,
                notice_list_url,
            )

    return await _fetch_latest_notice_items_with_client(client, notice_list_url)


async def fetch_latest_event_items(
    event_list_url: str = MAPLELAND_EVENT_LIST_URL,
    client: httpx.AsyncClient | None = None,
) -> list[NoticeItem]:
    """Fetch latest Mapleland event titles and URLs."""
    return await _fetch_latest_board_items(
        event_list_url,
        MAPLELAND_EVENT_PATH_PREFIX,
        client,
    )


async def fetch_latest_devlog_items(
    devlog_list_url: str = MAPLELAND_DEVLOG_LIST_URL,
    client: httpx.AsyncClient | None = None,
) -> list[NoticeItem]:
    """Fetch latest Mapleland development log titles and URLs."""
    return await _fetch_latest_board_items(
        devlog_list_url,
        MAPLELAND_DEVLOG_PATH_PREFIX,
        client,
    )


def parse_notice_items(
    html: str,
    base_url: str = MAPLELAND_NOTICE_LIST_URL,
) -> list[NoticeItem]:
    """Parse Mapleland notice items from a notice list HTML document."""
    return _parse_board_items(html, base_url, MAPLELAND_NOTICE_PATH_PREFIX)


def parse_event_items(
    html: str,
    base_url: str = MAPLELAND_EVENT_LIST_URL,
) -> list[NoticeItem]:
    """Parse Mapleland event items from an event list HTML document."""
    return _parse_board_items(html, base_url, MAPLELAND_EVENT_PATH_PREFIX)


def parse_devlog_items(
    html: str,
    base_url: str = MAPLELAND_DEVLOG_LIST_URL,
) -> list[NoticeItem]:
    """Parse Mapleland development log items from a devlog list HTML document."""
    return _parse_board_items(html, base_url, MAPLELAND_DEVLOG_PATH_PREFIX)


async def _fetch_latest_board_items(
    board_list_url: str,
    detail_path_prefix: str,
    client: httpx.AsyncClient | None,
) -> list[NoticeItem]:
    if client is None:
        async with httpx.AsyncClient(
            timeout=DEFAULT_MAPLELAND_REQUEST_TIMEOUT_SECONDS
        ) as default_client:
            return await _fetch_board_items_with_client(
                default_client,
                board_list_url,
                detail_path_prefix,
            )
    return await _fetch_board_items_with_client(client, board_list_url, detail_path_prefix)


def _parse_board_items(
    html: str,
    base_url: str,
    detail_path_prefix: str,
) -> list[NoticeItem]:
    soup = BeautifulSoup(html, "html.parser")
    notice_items: list[NoticeItem] = []
    seen_urls: set[str] = set()

    for link in soup.find_all("a", href=True):
        href = str(link["href"])
        if not _is_board_detail_href(href, detail_path_prefix):
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


async def _fetch_latest_notice_items_with_client(
    client: httpx.AsyncClient,
    notice_list_url: str,
) -> list[NoticeItem]:
    try:
        response = await client.get(
            notice_list_url,
            timeout=DEFAULT_MAPLELAND_REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as error:
        raise MaplelandCrawlerError("Mapleland notice page returned an HTTP error.") from error
    except httpx.RequestError as error:
        raise MaplelandCrawlerError("Failed to request Mapleland notice page.") from error

    return _parse_board_items(
        response.text,
        notice_list_url,
        MAPLELAND_NOTICE_PATH_PREFIX,
    )


async def _fetch_board_items_with_client(
    client: httpx.AsyncClient,
    board_list_url: str,
    detail_path_prefix: str,
) -> list[NoticeItem]:
    try:
        response = await client.get(
            board_list_url,
            timeout=DEFAULT_MAPLELAND_REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as error:
        raise MaplelandCrawlerError("Mapleland board page returned an HTTP error.") from error
    except httpx.RequestError as error:
        raise MaplelandCrawlerError("Failed to request Mapleland board page.") from error
    return _parse_board_items(response.text, board_list_url, detail_path_prefix)


def _is_board_detail_href(href: str, detail_path_prefix: str) -> bool:
    parsed_href = urlparse(href)
    return parsed_href.path.startswith(detail_path_prefix)


def _clean_notice_title(title: str) -> str:
    if title.endswith("N"):
        return title[:-1].strip()
    return title.strip()
