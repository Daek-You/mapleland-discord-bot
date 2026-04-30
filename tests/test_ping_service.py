from app.services.ping_service import get_ping_response


def test_get_ping_response_returns_pong() -> None:
    assert get_ping_response() == "Pong!"
