import asyncio

import httpx
import pytest

from app.config import MAPLENOTE_MONSTER_LIST_URL
from app.crawler.maplenote import (
    MapleNoteCrawlerError,
    MonsterDetail,
    MonsterDropItem,
    MonsterSummary,
    fetch_monster_detail,
    parse_drop_items,
    parse_monster_detail,
    parse_monster_summaries,
    search_monster_summaries,
)

MONSTER_LIST_HTML = """
<html>
  <body>
    <a href="https://xn--o80b01o9mlw3kdzc.com/monster_card/210100" class="monster-card-link">
      <div class="monster-card">
        <div class="monster-name"><p>슬라임</p></div>
        <div class="monster-image-box">
          <img src="http://maplestory.io/api/gms/200/mob/animated/210100/stand" alt="슬라임">
        </div>
        <div class="monster-stats">
          <p>LV : 6</p>
          <p>HP : 50</p>
          <p>MP : 35</p>
          <p>EXP : 10</p>
          <p>속성 : <span class="ele-name">전기속성약점</span></p>
        </div>
      </div>
    </a>
    <a href="/monster_card/1210102" class="monster-card-link">
      <div class="monster-card">
        <div class="monster-name"><p>버블링</p></div>
        <div class="monster-stats">
          <p>LV : 15</p>
          <p>HP : 240</p>
          <p>MP : 10</p>
          <p>EXP : 26</p>
          <p>속성 : -</p>
        </div>
      </div>
    </a>
  </body>
</html>
"""

MONSTER_DETAIL_HTML = """
<html>
  <body>
    <div class="monster-card">
      <div class="card-header"><p>슬라임</p></div>
      <div class="monster-image-box">
        <img src="http://maplestory.io/api/gms/200/mob/animated/210100/stand" alt="슬라임">
      </div>
      <div class="monster-stats">
        <p>LV : 6</p>
        <p>HP : 50</p>
        <p>MP : 35</p>
        <p>EXP : 10</p>
        <p>속성 : <span class="ele-name">전기속성약점</span></p>
      </div>
    </div>
    <div class="drop-list">
      <a class="drop-item-row" href="/item_detail/4000004">
        <span class="drop-item-name" title="물컹물컹한 액체">물컹물컹한 액체</span>
        <span class="drop-item-value">40</span>
      </a>
      <a class="drop-item-row" href="/item_detail/2000000">
        <span class="drop-item-name" title="빨간 포션">빨간 포션</span>
        <span class="drop-item-value">1</span>
      </a>
    </div>
  </body>
</html>
"""

MONSTER_FULL_DETAIL_HTML = """
<html>
  <body>
    <div class="info-box main-info">
      <a href="/monster_card/210100">
        <img src="https://maplestory.io/api/KMS/300/item/4030012/icon" alt="카드 버튼">
      </a>
      <img src="http://maplestory.io/api/gms/100/mob/animated/210100/stand" alt="210100 이미지">
      <h2>슬라임</h2>
      <div class="dsc-box">
        <h3>Lv : 6</h3>
      </div>
    </div>
    <div class="info-box stats-info">
      <span class="hp-box">HP : 50</span>
      <span class="mp-box">MP : 35</span>
      <span class="exp-box">EXP : 10</span>
      <span class="acc">속성관계 : <div class="ele-name">전기속성약점</div></span>
      <h2>SPAWN</h2>
      <div class="spawn-box">
        <a href="/map_detail/100010000" class="block-link">
          <h3><img src="/map/icon"> 헤네시스 북쪽언덕</h3>
        </a>
        <a href="/map_detail/100030001" class="block-link">
          <h3><img src="/map/icon"> 파란버섯의 숲</h3>
        </a>
      </div>
    </div>
    <div class="info-box get-info">
      <a class="block-link drop-link" href="/item_detail/4000004">
        <div class="item-box drop-item-box">
          <img src="https://maplestory.io/api/gms/90/item/4000004/icon?resize=2" alt="물컹물컹한 액체">
          <div class="item-details"><h3>물컹물컹한 액체</h3></div>
          <div class="drop-rate-box">40%</div>
        </div>
      </a>
    </div>
  </body>
</html>
"""


class FakeResponse:
    def __init__(self, text: str, status_code: int = 200) -> None:
        self.text = text
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            request = httpx.Request("GET", MAPLENOTE_MONSTER_LIST_URL)
            response = httpx.Response(self.status_code, request=request)
            raise httpx.HTTPStatusError("HTTP error", request=request, response=response)


class FakeClient:
    def __init__(
        self,
        response: FakeResponse | None = None,
        request_error: httpx.RequestError | None = None,
    ) -> None:
        self.response = response
        self.request_error = request_error
        self.requested_url: str | None = None
        self.requested_params: dict[str, str] | None = None
        self.requested_timeout: float | None = None

    async def get(
        self,
        url: str,
        params: dict[str, str] | None = None,
        *,
        timeout: float | None = None,
    ) -> FakeResponse:
        self.requested_url = url
        self.requested_params = params
        self.requested_timeout = timeout
        if self.request_error:
            raise self.request_error
        if self.response is None:
            raise AssertionError("FakeClient requires a response or request_error.")
        return self.response


def test_parse_monster_summaries_returns_monster_list() -> None:
    summaries = parse_monster_summaries(MONSTER_LIST_HTML)

    assert summaries == [
        MonsterSummary(
            name="슬라임",
            level="6",
            hp="50",
            mp="35",
            exp="10",
            element="전기속성약점",
            detail_url="https://xn--o80b01o9mlw3kdzc.com/monster_card/210100",
            image_url="http://maplestory.io/api/gms/200/mob/animated/210100/stand",
        ),
        MonsterSummary(
            name="버블링",
            level="15",
            hp="240",
            mp="10",
            exp="26",
            element="-",
            detail_url="https://xn--o80b01o9mlw3kdzc.com/monster_card/1210102",
            image_url=None,
        ),
    ]


def test_parse_monster_detail_returns_stats_and_drops() -> None:
    detail = parse_monster_detail(
        MONSTER_DETAIL_HTML,
        detail_url="https://xn--o80b01o9mlw3kdzc.com/monster_card/210100",
    )

    assert detail == MonsterDetail(
        name="슬라임",
        level="6",
        hp="50",
        mp="35",
        exp="10",
        element="전기속성약점",
        detail_url="https://xn--o80b01o9mlw3kdzc.com/monster_card/210100",
        image_url="http://maplestory.io/api/gms/200/mob/animated/210100/stand",
        drop_items=[
            MonsterDropItem(
                name="물컹물컹한 액체",
                drop_rate="40",
                icon_url=None,
                detail_url="https://xn--o80b01o9mlw3kdzc.com/item_detail/4000004",
            ),
            MonsterDropItem(
                name="빨간 포션",
                drop_rate="1",
                icon_url=None,
                detail_url="https://xn--o80b01o9mlw3kdzc.com/item_detail/2000000",
            ),
        ],
        spawn_locations=[],
    )


def test_parse_monster_full_detail_returns_spawn_and_drop_icons() -> None:
    detail = parse_monster_detail(
        MONSTER_FULL_DETAIL_HTML,
        detail_url="https://xn--o80b01o9mlw3kdzc.com/monster_detail/210100?from=card",
    )

    assert detail.name == "슬라임"
    assert detail.level == "6"
    assert detail.hp == "50"
    assert detail.mp == "35"
    assert detail.exp == "10"
    assert detail.element == "전기속성약점"
    assert detail.image_url == "http://maplestory.io/api/gms/100/mob/animated/210100/stand"
    assert detail.spawn_locations == ["헤네시스 북쪽언덕", "파란버섯의 숲"]
    assert detail.drop_items == [
        MonsterDropItem(
            name="물컹물컹한 액체",
            drop_rate="40%",
            icon_url="https://maplestory.io/api/gms/90/item/4000004/icon?resize=2",
            detail_url="https://xn--o80b01o9mlw3kdzc.com/item_detail/4000004",
        )
    ]


def test_parse_drop_items_falls_back_to_drop_slot_names() -> None:
    html = """
    <div class="drop-slot" data-name="주문서"></div>
    <div class="drop-slot"></div>
    <div class="drop-slot" data-name="빨간 포션"></div>
    """

    assert parse_drop_items(html) == [
        MonsterDropItem(name="주문서", drop_rate=""),
        MonsterDropItem(name="빨간 포션", drop_rate=""),
    ]


def test_search_monster_summaries_uses_query_param() -> None:
    client = FakeClient(response=FakeResponse(MONSTER_LIST_HTML))

    summaries = asyncio.run(search_monster_summaries("슬라임", client=client))

    assert client.requested_url == MAPLENOTE_MONSTER_LIST_URL
    assert client.requested_params == {"q": "슬라임"}
    assert client.requested_timeout is not None
    assert summaries[0].name == "슬라임"


def test_fetch_monster_detail_wraps_http_error() -> None:
    client = FakeClient(response=FakeResponse("server error", status_code=500))

    with pytest.raises(MapleNoteCrawlerError, match="HTTP error"):
        asyncio.run(
            fetch_monster_detail("https://example.com/monster_card/1", client=client)
        )


def test_fetch_monster_detail_requests_full_detail_page_from_card_url() -> None:
    client = FakeClient(response=FakeResponse(MONSTER_FULL_DETAIL_HTML))

    asyncio.run(
        fetch_monster_detail(
            "https://xn--o80b01o9mlw3kdzc.com/monster_card/210100",
            client=client,
        )
    )

    assert (
        client.requested_url
        == "https://xn--o80b01o9mlw3kdzc.com/monster_detail/210100?from=card"
    )
    assert client.requested_timeout is not None


def test_search_monster_summaries_wraps_network_error() -> None:
    request = httpx.Request("GET", MAPLENOTE_MONSTER_LIST_URL)
    client = FakeClient(request_error=httpx.ConnectError("connection failed", request=request))

    with pytest.raises(MapleNoteCrawlerError, match="request"):
        asyncio.run(search_monster_summaries("슬라임", client=client))


def test_parse_monster_detail_raises_error_for_unexpected_html() -> None:
    with pytest.raises(MapleNoteCrawlerError, match="structure"):
        parse_monster_detail(
            "<html><body><p>unexpected</p></body></html>",
            detail_url="https://example.com/monster_card/1",
        )
