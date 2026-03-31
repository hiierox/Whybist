from unittest.mock import AsyncMock, Mock

import pytest

from app.service import app


@pytest.mark.asyncio
async def test_search_film_by_keyword(client):
    keyword = 'matrix'
    payload = {
        'keyword': keyword,
        'pagesCount': 1,
        'films': [{'filmId': 301}],
    }
    response_mock = Mock(status_code=200)
    response_mock.json.return_value = payload

    http_client_mock = Mock()
    http_client_mock.get = AsyncMock(return_value=response_mock)
    app.state.http_client = http_client_mock

    response = await client.get('/film', params={'keyword': keyword, 'page': 1})

    assert response.status_code == 200
    data = response.json()
    assert data['keyword'] == keyword
    assert data['pagesCount'] == 1
    assert len(data['films']) == 1
    assert data['films'][0]['filmId'] == 301
    http_client_mock.get.assert_awaited_once_with(
        '/api/v2.1/films/search-by-keyword',
        params={'keyword': keyword, 'page': 1},
    )
