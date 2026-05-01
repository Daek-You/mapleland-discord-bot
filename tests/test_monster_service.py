import logging

from app.crawler.maplenote import (
    MapleNoteCrawlerError,
    MonsterDetail,
    MonsterDropItem,
    MonsterSummary,
)
from app.services.monster_service import (
    MONSTER_CANDIDATE_HEADER,
    MONSTER_SEARCH_EMPTY_MESSAGE,
    MONSTER_SEARCH_FAILURE_MESSAGE,
    get_monster_drop_search_response,
    get_monster_search_response,
)


SLIME_SUMMARY = MonsterSummary(
    name="슬라임",
    level="6",
    hp="50",
    mp="35",
    exp="10",
    element="전기속성약점",
    detail_url="https://example.com/monster_card/210100",
    image_url="https://example.com/slime.png",
)

KING_SLIME_SUMMARY = MonsterSummary(
    name="킹슬라임",
    level="40",
    hp="8,000",
    mp="100",
    exp="800",
    element="불속성반감",
    detail_url="https://example.com/monster_card/9300003",
    image_url=None,
)

SLIME_DETAIL = MonsterDetail(
    name="슬라임",
    level="6",
    hp="50",
    mp="35",
    exp="10",
    element="전기속성약점",
    detail_url="https://example.com/monster_card/210100",
    image_url="https://example.com/slime.png",
    drop_items=[
        MonsterDropItem(
            name="물컹물컹한 액체",
            drop_rate="40%",
            icon_url="https://example.com/item/4000004.png",
            detail_url="https://example.com/item_detail/4000004",
        ),
        MonsterDropItem(
            name="빨간 포션",
            drop_rate="1%",
            icon_url="https://example.com/item/2000000.png",
            detail_url="https://example.com/item_detail/2000000",
        ),
        MonsterDropItem(name="슬라임의 방울", drop_rate="3%"),
    ],
    spawn_locations=["헤네시스 북쪽언덕", "파란버섯의 숲"],
)


def test_get_monster_search_response_selects_exact_match() -> None:
    def get_detail(detail_url: str) -> MonsterDetail:
        assert detail_url == SLIME_SUMMARY.detail_url
        return SLIME_DETAIL

    response = get_monster_search_response(
        "슬라임",
        search_summaries=lambda query: [KING_SLIME_SUMMARY, SLIME_SUMMARY],
        get_detail=get_detail,
    )

    assert response.content is None
    assert response.embed is not None
    assert response.embed.title == "슬라임"
    assert response.embed.description == ""
    assert response.embed.footer == ""
    assert response.embed.url == "https://example.com/monster_card/210100"
    assert response.embed.thumbnail_url == "https://example.com/slime.png"
    assert response.embed.fields[0].name == "기본 정보"
    assert "LV: 6" in response.embed.fields[0].value
    assert response.embed.fields[1].value == "전기속성약점"
    assert "헤네시스 북쪽언덕" in response.embed.fields[2].value
    assert all(field.name != "주요 드랍 아이템" for field in response.embed.fields)
    assert response.embeds is None


def test_get_monster_search_response_limits_spawn_locations() -> None:
    many_spawn_detail = MonsterDetail(
        name="슬라임",
        level="6",
        hp="50",
        mp="35",
        exp="10",
        element="-",
        detail_url="https://example.com/monster_detail/210100?from=card",
        image_url=None,
        spawn_locations=[f"스폰 장소 {index}" for index in range(1, 12)],
    )

    response = get_monster_search_response(
        "슬라임",
        search_summaries=lambda query: [SLIME_SUMMARY],
        get_detail=lambda detail_url: many_spawn_detail,
    )

    assert response.embed is not None
    spawn_field = response.embed.fields[2].value
    assert "스폰 장소 10" in spawn_field
    assert "스폰 장소 11" not in spawn_field
    assert "외 1곳" in spawn_field
    assert "상세 페이지" not in spawn_field
    assert len(response.embed.fields) == 3


def test_get_monster_search_response_returns_candidates_for_partial_matches() -> None:
    response = get_monster_search_response(
        "슬",
        search_summaries=lambda query: [SLIME_SUMMARY, KING_SLIME_SUMMARY],
        get_detail=lambda detail_url: SLIME_DETAIL,
    )

    assert response.embed is None
    assert response.content is not None
    message = response.content
    assert message.startswith(MONSTER_CANDIDATE_HEADER)
    assert "1. [슬라임](https://example.com/monster_card/210100) - LV 6" in message
    assert "2. [킹슬라임](https://example.com/monster_card/9300003) - LV 40" in message


def test_get_monster_search_response_returns_empty_message_for_no_results(caplog) -> None:
    with caplog.at_level(logging.WARNING):
        response = get_monster_search_response(
            "없는몹",
            search_summaries=lambda query: [],
            get_detail=lambda detail_url: SLIME_DETAIL,
        )

    assert response.content == MONSTER_SEARCH_EMPTY_MESSAGE
    assert response.embed is None
    assert "Monster search returned no results." in caplog.text


def test_get_monster_drop_search_response_includes_items_without_icons() -> None:
    many_drop_detail = MonsterDetail(
        name="슬라임",
        level="6",
        hp="50",
        mp="35",
        exp="10",
        element="-",
        detail_url="https://example.com/monster_card/210100",
        image_url=None,
        drop_items=[
            MonsterDropItem(name=f"아이템 {index}", drop_rate=f"{index}%")
            for index in range(1, 12)
        ],
    )

    response = get_monster_drop_search_response(
        "슬라임",
        search_summaries=lambda query: [SLIME_SUMMARY],
        get_detail=lambda detail_url: many_drop_detail,
    )

    assert response.content == "**슬라임 주요 드랍 아이템**"
    assert response.embeds is None
    assert response.drop_items is not None
    assert len(response.drop_items) == 11
    assert response.drop_items[0].name == "아이템 1"
    assert response.drop_items[0].icon_url is None


def test_get_monster_drop_search_response_returns_all_drop_items_for_pagination() -> None:
    many_drop_detail = MonsterDetail(
        name="슬라임",
        level="6",
        hp="50",
        mp="35",
        exp="10",
        element="-",
        detail_url="https://example.com/monster_card/210100",
        image_url=None,
        drop_items=[
            MonsterDropItem(
                name=f"아이템 {index}",
                drop_rate=f"{index}%",
                icon_url=f"https://example.com/item/{index}.png",
            )
            for index in range(1, 12)
        ],
    )

    response = get_monster_drop_search_response(
        "슬라임",
        search_summaries=lambda query: [SLIME_SUMMARY],
        get_detail=lambda detail_url: many_drop_detail,
    )

    assert response.drop_items is not None
    assert len(response.drop_items) == 11
    assert response.drop_items[-1].name == "아이템 11"
    assert response.monster_detail_url == "https://example.com/monster_card/210100"


def test_get_monster_drop_search_response_returns_drop_items() -> None:
    response = get_monster_drop_search_response(
        "슬라임",
        search_summaries=lambda query: [SLIME_SUMMARY],
        get_detail=lambda detail_url: SLIME_DETAIL,
    )

    assert response.content == "**슬라임 주요 드랍 아이템**"
    assert response.embeds is None
    assert response.drop_items is not None
    assert response.drop_items[0].name == "물컹물컹한 액체"
    assert response.drop_items[0].drop_rate == "40%"
    assert response.drop_items[0].icon_url == "https://example.com/item/4000004.png"


def test_get_monster_drop_search_response_logs_missing_drop_items(caplog) -> None:
    detail_without_drops = MonsterDetail(
        name="슬라임",
        level="6",
        hp="50",
        mp="35",
        exp="10",
        element="-",
        detail_url="https://example.com/monster_card/210100",
        image_url=None,
        drop_items=[],
    )

    with caplog.at_level(logging.WARNING):
        response = get_monster_drop_search_response(
            "슬라임",
            search_summaries=lambda query: [SLIME_SUMMARY],
            get_detail=lambda detail_url: detail_without_drops,
        )

    assert response.content == "등록된 드랍 아이템이 없어요."
    assert "Monster drop search found no drop items." in caplog.text


def test_get_monster_search_response_returns_failure_message_on_crawler_error() -> None:
    def raise_crawler_error(query: str) -> list[MonsterSummary]:
        raise MapleNoteCrawlerError("failed")

    response = get_monster_search_response(
        "슬라임",
        search_summaries=raise_crawler_error,
        get_detail=lambda detail_url: SLIME_DETAIL,
    )

    assert response.content == MONSTER_SEARCH_FAILURE_MESSAGE
    assert response.embed is None
