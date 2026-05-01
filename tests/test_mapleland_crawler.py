import httpx
import pytest

from app.crawler.mapleland import (
    MAPLELAND_NOTICE_LIST_URL,
    MaplelandCrawlerError,
    NoticeItem,
    fetch_latest_notice_items,
    parse_notice_items,
)


NOTICE_LIST_HTML = """
<html>
  <body>
    <h1>공지사항</h1>
    <a href="/board/notices/first-notice-id">2026년 4월 30일(목) 무중단 배포 안내 N</a>
    <a href="/board/notices/second-notice-id">2026년 4월 30일(목) 패치노트</a>
    <a href="/board/events/event-id">이벤트 글은 제외됩니다</a>
  </body>
</html>
"""


class FakeResponse:
    def __init__(self, text: str, status_code: int = 200) -> None:
        self.text = text
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            request = httpx.Request("GET", MAPLELAND_NOTICE_LIST_URL)
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

    def get(self, url: str) -> FakeResponse:
        self.requested_url = url
        if self.request_error:
            raise self.request_error
        if self.response is None:
            raise AssertionError("FakeClient requires a response or request_error.")
        return self.response


def test_parse_notice_items_returns_multiple_notice_titles_and_urls() -> None:
    notice_items = parse_notice_items(NOTICE_LIST_HTML)

    assert notice_items == [
        NoticeItem(
            title="2026년 4월 30일(목) 무중단 배포 안내",
            url="https://maple.land/board/notices/first-notice-id",
        ),
        NoticeItem(
            title="2026년 4월 30일(목) 패치노트",
            url="https://maple.land/board/notices/second-notice-id",
        ),
    ]


def test_parse_notice_items_returns_empty_list_for_unexpected_html() -> None:
    notice_items = parse_notice_items("<html><body><p>공지 목록이 없습니다.</p></body></html>")

    assert notice_items == []


def test_fetch_latest_notice_items_uses_client_and_parses_response() -> None:
    client = FakeClient(response=FakeResponse(NOTICE_LIST_HTML))

    notice_items = fetch_latest_notice_items(client=client)

    assert client.requested_url == MAPLELAND_NOTICE_LIST_URL
    assert len(notice_items) == 2


def test_fetch_latest_notice_items_wraps_http_error() -> None:
    client = FakeClient(response=FakeResponse("server error", status_code=500))

    with pytest.raises(MaplelandCrawlerError, match="HTTP error"):
        fetch_latest_notice_items(client=client)


def test_fetch_latest_notice_items_wraps_network_error() -> None:
    request = httpx.Request("GET", MAPLELAND_NOTICE_LIST_URL)
    client = FakeClient(request_error=httpx.ConnectError("connection failed", request=request))

    with pytest.raises(MaplelandCrawlerError, match="request"):
        fetch_latest_notice_items(client=client)
