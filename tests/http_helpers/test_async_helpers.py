import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from py_clob_client.http_helpers.helpers import (
    async_request,
    async_get,
    async_post,
    async_delete,
    async_put,
    GET,
    POST,
    DELETE,
    PUT,
)
from py_clob_client.exceptions import PolyApiException


@pytest.fixture
def mock_response():
    """Create a mock response object"""
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"success": True}
    return response


@pytest.fixture
def mock_error_response():
    """Create a mock error response object"""
    response = MagicMock()
    response.status_code = 400
    response.text = "Bad Request"
    return response


class TestAsyncHelpers:
    @pytest.mark.asyncio
    async def test_async_request_get_success(self, mock_response):
        """Test async_request with GET method returns JSON response"""
        with patch(
            "py_clob_client.http_helpers.helpers._async_http_client.request",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_request:
            result = await async_request("http://test.com/api", GET)

            assert result == {"success": True}
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_request_post_with_json_data(self, mock_response):
        """Test async_request with POST method and JSON data"""
        with patch(
            "py_clob_client.http_helpers.helpers._async_http_client.request",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_request:
            data = {"key": "value"}
            result = await async_request("http://test.com/api", POST, data=data)

            assert result == {"success": True}
            mock_request.assert_called_once()
            call_kwargs = mock_request.call_args[1]
            assert call_kwargs["json"] == data

    @pytest.mark.asyncio
    async def test_async_request_post_with_serialized_data(self, mock_response):
        """Test async_request with POST method and pre-serialized string data"""
        with patch(
            "py_clob_client.http_helpers.helpers._async_http_client.request",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_request:
            data = '{"key":"value"}'
            result = await async_request("http://test.com/api", POST, data=data)

            assert result == {"success": True}
            mock_request.assert_called_once()
            call_kwargs = mock_request.call_args[1]
            assert call_kwargs["content"] == data.encode("utf-8")

    @pytest.mark.asyncio
    async def test_async_request_error_status(self, mock_error_response):
        """Test async_request raises PolyApiException on error status"""
        with patch(
            "py_clob_client.http_helpers.helpers._async_http_client.request",
            new_callable=AsyncMock,
            return_value=mock_error_response,
        ):
            with pytest.raises(PolyApiException):
                await async_request("http://test.com/api", GET)

    @pytest.mark.asyncio
    async def test_async_request_text_response(self, mock_response):
        """Test async_request returns text when JSON parsing fails"""
        mock_response.json.side_effect = ValueError("Not JSON")
        mock_response.text = "Plain text response"

        with patch(
            "py_clob_client.http_helpers.helpers._async_http_client.request",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await async_request("http://test.com/api", GET)
            assert result == "Plain text response"

    @pytest.mark.asyncio
    async def test_async_get(self, mock_response):
        """Test async_get calls async_request with GET method"""
        with patch(
            "py_clob_client.http_helpers.helpers._async_http_client.request",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_request:
            result = await async_get("http://test.com/api", headers={"Auth": "token"})

            assert result == {"success": True}
            call_kwargs = mock_request.call_args[1]
            assert call_kwargs["method"] == GET

    @pytest.mark.asyncio
    async def test_async_post(self, mock_response):
        """Test async_post calls async_request with POST method"""
        with patch(
            "py_clob_client.http_helpers.helpers._async_http_client.request",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_request:
            result = await async_post(
                "http://test.com/api", headers={"Auth": "token"}, data={"key": "value"}
            )

            assert result == {"success": True}
            call_kwargs = mock_request.call_args[1]
            assert call_kwargs["method"] == POST

    @pytest.mark.asyncio
    async def test_async_delete(self, mock_response):
        """Test async_delete calls async_request with DELETE method"""
        with patch(
            "py_clob_client.http_helpers.helpers._async_http_client.request",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_request:
            result = await async_delete("http://test.com/api")

            assert result == {"success": True}
            call_kwargs = mock_request.call_args[1]
            assert call_kwargs["method"] == DELETE

    @pytest.mark.asyncio
    async def test_async_put(self, mock_response):
        """Test async_put calls async_request with PUT method"""
        with patch(
            "py_clob_client.http_helpers.helpers._async_http_client.request",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_request:
            result = await async_put("http://test.com/api", data={"update": "data"})

            assert result == {"success": True}
            call_kwargs = mock_request.call_args[1]
            assert call_kwargs["method"] == PUT

    @pytest.mark.asyncio
    async def test_async_request_headers_overload(self, mock_response):
        """Test that headers are properly overloaded with default values"""
        with patch(
            "py_clob_client.http_helpers.helpers._async_http_client.request",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_request:
            await async_get("http://test.com/api", headers={"Custom": "header"})

            call_kwargs = mock_request.call_args[1]
            headers = call_kwargs["headers"]
            assert headers["User-Agent"] == "py_clob_client"
            assert headers["Content-Type"] == "application/json"
            assert headers["Custom"] == "header"
