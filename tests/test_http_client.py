import asyncio

from app.http_client import DEFAULT_HTTP_USER_AGENT, create_shared_http_client


def test_create_shared_http_client_sets_identifiable_user_agent() -> None:
    async def scenario() -> None:
        client = create_shared_http_client()
        try:
            assert client.headers["User-Agent"] == DEFAULT_HTTP_USER_AGENT
        finally:
            await client.aclose()

    asyncio.run(scenario())
