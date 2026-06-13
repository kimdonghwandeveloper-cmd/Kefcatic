"""Google Sheets connector tests (httpx.MockTransport, no DB)."""
import json

import pytest

from tests._connector_mock import patch_google_token, patch_http, route


def _connector(monkeypatch, handler, config=None):
    patch_google_token(monkeypatch, "google_sheets")
    captured = patch_http(monkeypatch, handler)
    from app.connectors.google_sheets import GoogleSheetsConnector

    conn = GoogleSheetsConnector(
        credentials={"access_token": "t", "refresh_token": "r"}, config=config
    )
    return conn, captured


@pytest.mark.asyncio
async def test_list_items(monkeypatch):
    files = {
        "files": [
            {
                "id": "sheet1",
                "name": "Budget 2026",
                "createdTime": "2026-01-01T00:00:00Z",
                "webViewLink": "https://sheets/sheet1",
            }
        ]
    }
    conn, captured = _connector(monkeypatch, route({"/files": {"json": files}}))
    items = await conn.list_items()
    assert len(items) == 1
    assert items[0].id == "sheet1"
    # only spreadsheets requested
    assert "spreadsheet" in str(captured[0].url)


@pytest.mark.asyncio
async def test_read_item(monkeypatch):
    values = {
        "range": "Sheet1!A1:C2",
        "majorDimension": "ROWS",
        "values": [["Name", "Amount"], ["Rent", "1000"]],
    }
    conn, captured = _connector(monkeypatch, route({"/values/": {"json": values}}))
    item = await conn.read_item("sheet1")
    assert item.content == [["Name", "Amount"], ["Rent", "1000"]]
    assert item.metadata["range"] == "Sheet1!A1:C2"


@pytest.mark.asyncio
async def test_create_item_appends_rows(monkeypatch):
    result = {
        "updates": {
            "updatedRange": "Sheet1!A3:B3",
            "updatedRows": 1,
            "updatedCells": 2,
        }
    }
    conn, captured = _connector(monkeypatch, route({":append": {"json": result}}))
    item = await conn.create_item(
        {"spreadsheet_id": "sheet1", "values": [["Food", "50"]]}
    )
    assert item.metadata["updated_rows"] == 1
    assert captured[0].method == "POST"
    body = json.loads(captured[0].content)
    assert body["values"] == [["Food", "50"]]
    assert "valueInputOption=USER_ENTERED" in str(captured[0].url)


@pytest.mark.asyncio
async def test_update_item_overwrites(monkeypatch):
    result = {"updatedRange": "Sheet1!A1:B1", "updatedCells": 2}
    conn, captured = _connector(monkeypatch, route({"/values/": {"json": result}}))
    item = await conn.update_item(
        "sheet1", {"range": "Sheet1!A1:B1", "values": [["X", "Y"]]}
    )
    assert item.metadata["updated_cells"] == 2
    assert captured[0].method == "PUT"
