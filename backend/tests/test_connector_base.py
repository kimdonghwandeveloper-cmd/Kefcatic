"""Unit tests for the Connector SDK base and YouTube connector (mocked)."""
import pytest
import httpx

from app.connectors.base import CONNECTOR_REGISTRY, ConnectorItem
from app.connectors.youtube import YouTubeConnector


def test_youtube_registered():
    assert "youtube" in CONNECTOR_REGISTRY
    assert CONNECTOR_REGISTRY["youtube"] is YouTubeConnector


@pytest.mark.asyncio
async def test_list_items_mock():
    """Verify list_items parses the YouTube API response correctly."""
    mock_response = {
        "items": [
            {
                "id": "comment-thread-1",
                "snippet": {
                    "totalReplyCount": 0,
                    "topLevelComment": {
                        "snippet": {
                            "textDisplay": "Great video!",
                            "authorDisplayName": "Alice",
                            "likeCount": 5,
                            "videoId": "vid-1",
                            "publishedAt": "2026-01-01T00:00:00Z",
                        }
                    },
                },
            }
        ]
    }

    # Stub out the channel-id call and the comment threads call
    channel_response = {"items": [{"id": "channel-1"}]}

    def handler(request: httpx.Request) -> httpx.Response:
        if "channels" in str(request.url):
            return httpx.Response(200, json=channel_response)
        return httpx.Response(200, json=mock_response)

    transport = httpx.MockTransport(handler)

    connector = YouTubeConnector(credentials={"access_token": "test-token"})
    # Patch the AsyncClient transport
    import httpx as _httpx
    original = _httpx.AsyncClient

    class _PatchedClient(_httpx.AsyncClient):
        def __init__(self, **kwargs):
            kwargs["transport"] = transport
            super().__init__(**kwargs)

    _httpx.AsyncClient = _PatchedClient
    try:
        items = await connector.list_items(max_results=10)
    finally:
        _httpx.AsyncClient = original

    assert len(items) == 1
    assert items[0].id == "comment-thread-1"
    assert items[0].content == "Great video!"
    assert items[0].metadata["author"] == "Alice"
