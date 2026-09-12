"""Crawler for MapleNote Classic monster pages."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
from bs4.element import Tag

from app.config import (
    DEFAULT_MAPLENOTE_REQUEST_TIMEOUT_SECONDS,
    MAPLENOTE_BASE_URL,
    MAPLENOTE_MONSTER_LIST_URL,
)


class MapleNoteCrawlerError(RuntimeError):
    """Raised when MapleNote monster crawling fails."""


@dataclass(frozen=True)
class MonsterDropItem:
    """A monster drop item."""

    name: str
    drop_rate: str
    icon_url: str | None = None
    detail_url: str | None = None


@dataclass(frozen=True)
class MonsterSummary:
    """A monster result from the list page."""

    name: str
    level: str
    hp: str
    mp: str
    exp: str
    element: str
    detail_url: str
    image_url: str | None = None


@dataclass(frozen=True)
class MonsterDetail(MonsterSummary):
    """Detailed monster information."""

    drop_items: list[MonsterDropItem] | None = None
    spawn_locations: list[str] | None = None


async def search_monster_summaries(
    query: str,
    client: httpx.AsyncClient | None = None,
) -> list[MonsterSummary]:
    """Fetch and parse monster list results for a query."""
    if client is None:
        async with httpx.AsyncClient(
            timeout=DEFAULT_MAPLENOTE_REQUEST_TIMEOUT_SECONDS
        ) as default_client:
            return await _search_monster_summaries_with_client(default_client, query)

    return await _search_monster_summaries_with_client(client, query)


async def fetch_monster_detail(
    detail_url: str,
    client: httpx.AsyncClient | None = None,
) -> MonsterDetail:
    """Fetch and parse one monster detail page."""
    if client is None:
        async with httpx.AsyncClient(
            timeout=DEFAULT_MAPLENOTE_REQUEST_TIMEOUT_SECONDS
        ) as default_client:
            return await _fetch_monster_detail_with_client(default_client, detail_url)

    return await _fetch_monster_detail_with_client(client, detail_url)


def parse_monster_summaries(html: str, base_url: str = MAPLENOTE_BASE_URL) -> list[MonsterSummary]:
    """Parse monster summaries from a MapleNote list HTML document."""
    soup = BeautifulSoup(html, "html.parser")
    summaries: list[MonsterSummary] = []

    for link in soup.select("a.monster-card-link"):
        if not isinstance(link, Tag):
            continue

        card = link.select_one(".monster-card") or link
        name = _get_text(card.select_one(".monster-name p"))
        href = str(link.get("href", "")).strip()
        if not name or not href:
            continue

        summaries.append(
            MonsterSummary(
                name=name,
                level=_get_stat_value(card, "LV"),
                hp=_get_stat_value(card, "HP"),
                mp=_get_stat_value(card, "MP"),
                exp=_get_stat_value(card, "EXP"),
                element=_get_stat_value(card, "속성") or "-",
                detail_url=urljoin(base_url, href),
                image_url=_get_image_url(card, base_url),
            )
        )

    return summaries


def parse_monster_detail(html: str, detail_url: str) -> MonsterDetail:
    """Parse monster detail data from a MapleNote monster card page."""
    soup = BeautifulSoup(html, "html.parser")
    detail = _parse_monster_full_detail(soup, detail_url)
    if detail:
        return detail

    monster_card = soup.select_one(".monster-card")
    if not isinstance(monster_card, Tag):
        raise MapleNoteCrawlerError("Monster detail page structure was not recognized.")

    name = _get_text(monster_card.select_one(".card-header p"))
    if not name:
        raise MapleNoteCrawlerError("Monster detail page did not include a monster name.")

    return MonsterDetail(
        name=name,
        level=_get_stat_value(monster_card, "LV"),
        hp=_get_stat_value(monster_card, "HP"),
        mp=_get_stat_value(monster_card, "MP"),
        exp=_get_stat_value(monster_card, "EXP"),
        element=_get_stat_value(monster_card, "속성") or "-",
        detail_url=detail_url,
        image_url=_get_image_url(monster_card, MAPLENOTE_BASE_URL),
        drop_items=parse_drop_items(html),
        spawn_locations=[],
    )


def parse_drop_items(html: str) -> list[MonsterDropItem]:
    """Parse drop item names and values from a monster detail HTML document."""
    soup = BeautifulSoup(html, "html.parser")
    drop_items: list[MonsterDropItem] = []

    for drop_link in soup.select(".get-info a.drop-link"):
        name = _get_text(drop_link.select_one(".item-details h3"))
        drop_rate = _get_text(drop_link.select_one(".drop-rate-box"))
        if not name:
            continue

        drop_items.append(
            MonsterDropItem(
                name=name,
                drop_rate=drop_rate,
                icon_url=_get_image_url(drop_link, MAPLENOTE_BASE_URL),
                detail_url=urljoin(MAPLENOTE_BASE_URL, str(drop_link.get("href", ""))),
            )
        )

    if drop_items:
        return drop_items

    for item_row in soup.select(".drop-item-row"):
        name = _get_text(item_row.select_one(".drop-item-name"))
        value = _get_text(item_row.select_one(".drop-item-value"))
        if not name:
            continue
        drop_items.append(
            MonsterDropItem(
                name=name,
                drop_rate=value,
                icon_url=_get_image_url(item_row, MAPLENOTE_BASE_URL),
                detail_url=urljoin(MAPLENOTE_BASE_URL, str(item_row.get("href", ""))),
            )
        )

    if drop_items:
        return drop_items

    return [
        MonsterDropItem(name=str(drop_slot.get("data-name")).strip(), drop_rate="")
        for drop_slot in soup.select(".drop-slot[data-name]")
        if str(drop_slot.get("data-name", "")).strip()
    ]


def parse_spawn_locations(html: str) -> list[str]:
    """Parse monster spawn location names from a detail page."""
    soup = BeautifulSoup(html, "html.parser")
    return [
        _get_text(spawn_link.select_one("h3"))
        for spawn_link in soup.select(".spawn-box a")
        if _get_text(spawn_link.select_one("h3"))
    ]


async def _search_monster_summaries_with_client(
    client: httpx.AsyncClient,
    query: str,
) -> list[MonsterSummary]:
    try:
        response = await client.get(MAPLENOTE_MONSTER_LIST_URL, params={"q": query})
        response.raise_for_status()
    except httpx.HTTPStatusError as error:
        raise MapleNoteCrawlerError("MapleNote monster search returned an HTTP error.") from error
    except httpx.RequestError as error:
        raise MapleNoteCrawlerError("Failed to request MapleNote monster search.") from error

    return parse_monster_summaries(response.text)


async def _fetch_monster_detail_with_client(
    client: httpx.AsyncClient,
    detail_url: str,
) -> MonsterDetail:
    request_url = _get_monster_detail_url(detail_url)
    try:
        response = await client.get(request_url)
        response.raise_for_status()
    except httpx.HTTPStatusError as error:
        raise MapleNoteCrawlerError("MapleNote monster detail returned an HTTP error.") from error
    except httpx.RequestError as error:
        raise MapleNoteCrawlerError("Failed to request MapleNote monster detail.") from error

    return parse_monster_detail(response.text, detail_url=request_url)


def _parse_monster_full_detail(
    soup: BeautifulSoup,
    detail_url: str,
) -> MonsterDetail | None:
    main_info = soup.select_one(".main-info")
    if not isinstance(main_info, Tag):
        return None

    name = _get_text(main_info.select_one("h2"))
    if not name:
        return None

    stats_info = soup.select_one(".stats-info")
    return MonsterDetail(
        name=name,
        level=_get_prefixed_heading_value(main_info, "Lv"),
        hp=_get_box_value(stats_info, ".hp-box", "HP") if isinstance(stats_info, Tag) else "",
        mp=_get_box_value(stats_info, ".mp-box", "MP") if isinstance(stats_info, Tag) else "",
        exp=_get_box_value(stats_info, ".exp-box", "EXP") if isinstance(stats_info, Tag) else "",
        element=_get_full_detail_element(stats_info) if isinstance(stats_info, Tag) else "-",
        detail_url=detail_url,
        image_url=_get_image_url(main_info, MAPLENOTE_BASE_URL),
        drop_items=parse_drop_items(str(soup)),
        spawn_locations=parse_spawn_locations(str(soup)),
    )


def _get_monster_detail_url(url: str) -> str:
    if "/monster_card/" not in url:
        return url
    return url.replace("/monster_card/", "/monster_detail/") + "?from=card"


def _get_prefixed_heading_value(card: Tag, label: str) -> str:
    prefix = f"{label} :"
    for heading in card.select("h3"):
        text = _get_text(heading)
        if text.startswith(prefix):
            return text.removeprefix(prefix).strip()
    return ""


def _get_box_value(card: Tag, selector: str, label: str) -> str:
    prefix = f"{label} :"
    text = _get_text(card.select_one(selector))
    if text.startswith(prefix):
        return text.removeprefix(prefix).strip()
    return text


def _get_full_detail_element(card: Tag) -> str:
    element_names = [
        _get_text(element_name)
        for element_name in card.select(".ele-name")
        if _get_text(element_name)
    ]
    return ", ".join(element_names) or "-"


def _get_stat_value(card: Tag, label: str) -> str:
    prefix = f"{label} :"
    for paragraph in card.select(".monster-stats p"):
        text = _get_text(paragraph)
        if text.startswith(prefix):
            return text.removeprefix(prefix).strip()
    return ""


def _get_image_url(card: Tag, base_url: str) -> str | None:
    image = (
        card.select_one(".monster-image-box img")
        or card.select_one('img[alt$=" 이미지"]')
        or card.select_one("img")
    )
    if not isinstance(image, Tag):
        return None

    image_url = str(image.get("src", "")).strip()
    if not image_url:
        return None
    return urljoin(base_url, image_url)


def _get_text(element: Tag | None) -> str:
    if not isinstance(element, Tag):
        return ""
    return " ".join(element.get_text(" ", strip=True).split())
