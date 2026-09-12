"""Service logic for MapleNote monster search."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from app.config import (
    DEFAULT_MONSTER_CANDIDATE_DISPLAY_LIMIT,
    DEFAULT_MONSTER_DROP_DISPLAY_LIMIT,
    DEFAULT_MONSTER_SPAWN_DISPLAY_LIMIT,
)
from app.crawler.maplenote import (
    MapleNoteCrawlerError,
    MonsterDetail,
    MonsterDropItem,
    MonsterSummary,
    fetch_monster_detail,
    search_monster_summaries,
)


MONSTER_SEARCH_EMPTY_MESSAGE = "검색 결과가 없습니다."
MONSTER_SEARCH_FAILURE_MESSAGE = "몬스터 정보를 가져오지 못했습니다. 잠시 후 다시 시도해주세요."
MONSTER_CANDIDATE_HEADER = "**검색 후보**"
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MonsterSearchResult:
    """Selected monster detail or a candidate list."""

    detail: MonsterDetail | None
    candidates: list[MonsterSummary]


@dataclass(frozen=True)
class MonsterEmbedField:
    """A Discord embed field prepared by the service layer."""

    name: str
    value: str
    inline: bool = False


@dataclass(frozen=True)
class MonsterEmbedData:
    """Discord embed content prepared without importing Discord objects."""

    title: str
    description: str
    url: str
    thumbnail_url: str | None
    fields: list[MonsterEmbedField]
    footer: str


@dataclass(frozen=True)
class MonsterSearchResponse:
    """Discord-ready monster search response data."""

    content: str | None = None
    embed: MonsterEmbedData | None = None
    embeds: list[MonsterEmbedData] | None = None
    drop_items: list[MonsterDropItem] | None = None
    monster_detail_url: str | None = None


async def get_monster_search_response(
    query: str,
    search_summaries: Callable[[str], Awaitable[list[MonsterSummary]]] = search_monster_summaries,
    get_detail: Callable[[str], Awaitable[MonsterDetail]] = fetch_monster_detail,
    candidate_limit: int = DEFAULT_MONSTER_CANDIDATE_DISPLAY_LIMIT,
    drop_limit: int = DEFAULT_MONSTER_DROP_DISPLAY_LIMIT,
) -> MonsterSearchResponse:
    """Return a Discord-ready monster search response."""
    try:
        result = await search_monster(query, search_summaries, get_detail)
    except MapleNoteCrawlerError:
        logger.error("Failed to search MapleNote monster.", exc_info=True)
        return MonsterSearchResponse(content=MONSTER_SEARCH_FAILURE_MESSAGE)

    if result.detail:
        _log_missing_monster_detail_data(result.detail)
        return MonsterSearchResponse(
            embed=format_monster_detail_embed(result.detail),
        )
    if result.candidates:
        return MonsterSearchResponse(
            content=format_monster_candidates(
                result.candidates,
                candidate_limit=candidate_limit,
            )
        )
    logger.warning("Monster search returned no results.")
    return MonsterSearchResponse(content=MONSTER_SEARCH_EMPTY_MESSAGE)


async def get_monster_drop_search_response(
    query: str,
    search_summaries: Callable[[str], Awaitable[list[MonsterSummary]]] = search_monster_summaries,
    get_detail: Callable[[str], Awaitable[MonsterDetail]] = fetch_monster_detail,
    candidate_limit: int = DEFAULT_MONSTER_CANDIDATE_DISPLAY_LIMIT,
    drop_limit: int = DEFAULT_MONSTER_DROP_DISPLAY_LIMIT,
) -> MonsterSearchResponse:
    """Return a Discord-ready monster drop search response."""
    try:
        result = await search_monster(query, search_summaries, get_detail)
    except MapleNoteCrawlerError:
        logger.error("Failed to search MapleNote monster drops.", exc_info=True)
        return MonsterSearchResponse(content=MONSTER_SEARCH_FAILURE_MESSAGE)

    if result.detail:
        _log_missing_monster_detail_data(result.detail)
        drop_items = result.detail.drop_items or []
        if not drop_items:
            logger.warning("Monster drop search found no drop items.")
            return MonsterSearchResponse(content="등록된 드랍 아이템이 없어요.")
        return MonsterSearchResponse(
            content=f"**{result.detail.name} 주요 드랍 아이템**",
            drop_items=drop_items,
            monster_detail_url=result.detail.detail_url,
        )
    if result.candidates:
        return MonsterSearchResponse(
            content=format_monster_candidates(
                result.candidates,
                candidate_limit=candidate_limit,
            )
        )
    logger.warning("Monster drop search returned no results.")
    return MonsterSearchResponse(content=MONSTER_SEARCH_EMPTY_MESSAGE)


async def search_monster(
    query: str,
    search_summaries: Callable[[str], Awaitable[list[MonsterSummary]]] = search_monster_summaries,
    get_detail: Callable[[str], Awaitable[MonsterDetail]] = fetch_monster_detail,
) -> MonsterSearchResult:
    """Search a monster and fetch detail when one best match is selected."""
    normalized_query = _normalize_name(query)
    if not normalized_query:
        return MonsterSearchResult(detail=None, candidates=[])

    summaries = await search_summaries(query)
    matching_summaries = [
        summary
        for summary in summaries
        if normalized_query in _normalize_name(summary.name)
    ]
    exact_matches = [
        summary
        for summary in matching_summaries
        if _normalize_name(summary.name) == normalized_query
    ]

    selected_summary = exact_matches[0] if exact_matches else None
    if selected_summary is None and len(matching_summaries) == 1:
        selected_summary = matching_summaries[0]

    if selected_summary:
        return MonsterSearchResult(
            detail=await get_detail(selected_summary.detail_url),
            candidates=[],
        )

    return MonsterSearchResult(detail=None, candidates=matching_summaries)


def format_monster_detail_embed(
    monster: MonsterDetail,
    spawn_limit: int = DEFAULT_MONSTER_SPAWN_DISPLAY_LIMIT,
) -> MonsterEmbedData:
    """Format monster detail as Discord embed data."""
    spawn_text = _format_spawn_locations(monster, spawn_limit)
    stats = [
        f"LV: {monster.level or '-'}",
        f"HP: {monster.hp or '-'}",
        f"MP: {monster.mp or '-'}",
        f"EXP: {monster.exp or '-'}",
    ]

    return MonsterEmbedData(
        title=monster.name,
        description="",
        url=monster.detail_url,
        thumbnail_url=monster.image_url,
        fields=[
            MonsterEmbedField(name="기본 정보", value="\n".join(stats), inline=True),
            MonsterEmbedField(name="속성", value=monster.element or "-", inline=True),
            MonsterEmbedField(name="스폰 장소", value=spawn_text),
        ],
        footer="",
    )


def format_drop_item_embeds(
    monster: MonsterDetail,
    drop_limit: int = DEFAULT_MONSTER_DROP_DISPLAY_LIMIT,
) -> list[MonsterEmbedData]:
    """Format drop item icon embeds."""
    embeds: list[MonsterEmbedData] = []
    for drop_item in (monster.drop_items or [])[:drop_limit]:
        embeds.append(
            MonsterEmbedData(
                title=drop_item.name,
                description=f"드랍률: {drop_item.drop_rate or '-'}",
                url=drop_item.detail_url or monster.detail_url,
                thumbnail_url=drop_item.icon_url,
                fields=[],
                footer="",
            )
        )
    return embeds


def format_monster_candidates(
    candidates: list[MonsterSummary],
    candidate_limit: int = DEFAULT_MONSTER_CANDIDATE_DISPLAY_LIMIT,
) -> str:
    """Format monster candidates for ambiguous search results."""
    if not candidates:
        return MONSTER_SEARCH_EMPTY_MESSAGE

    candidate_lines = "\n".join(
        f"{index}. [{candidate.name}]({candidate.detail_url}) - LV {candidate.level or '-'}"
        for index, candidate in enumerate(candidates[:candidate_limit], start=1)
    )
    return f"{MONSTER_CANDIDATE_HEADER}\n{candidate_lines}"


def _normalize_name(name: str) -> str:
    return "".join(name.casefold().split())


def _log_missing_monster_detail_data(monster: MonsterDetail) -> None:
    missing_fields = [
        field_name
        for field_name, value in (
            ("level", monster.level),
            ("hp", monster.hp),
            ("mp", monster.mp),
            ("exp", monster.exp),
            ("element", monster.element),
            ("image_url", monster.image_url),
            ("spawn_locations", monster.spawn_locations),
        )
        if not value
    ]
    if missing_fields:
        logger.warning(
            "Monster detail data is missing expected fields: %s.",
            ", ".join(missing_fields),
        )


def _format_spawn_locations(monster: MonsterDetail, spawn_limit: int) -> str:
    spawn_locations = monster.spawn_locations or []
    if not spawn_locations:
        return "-"

    displayed_locations = spawn_locations[:spawn_limit]
    spawn_text = "\n".join(f"- {location}" for location in displayed_locations)
    remaining_count = len(spawn_locations) - len(displayed_locations)
    if remaining_count <= 0:
        return spawn_text

    return f"{spawn_text}\n외 {remaining_count}곳"
