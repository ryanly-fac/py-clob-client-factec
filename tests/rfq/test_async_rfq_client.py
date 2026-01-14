import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from py_clob_client.async_client import AsyncClobClient
from py_clob_client.rfq.async_rfq_client import AsyncRfqClient
from py_clob_client.clob_types import ApiCreds
from py_clob_client.rfq.rfq_types import (
    RfqUserRequest,
    RfqUserQuote,
    CancelRfqRequestParams,
    CancelRfqQuoteParams,
    GetRfqRequestsParams,
    GetRfqQuotesParams,
    GetRfqBestQuoteParams,
)
from py_clob_client.exceptions import PolyException


# Test constants
HOST = "https://clob.polymarket.com"
CHAIN_ID = 137
PRIVATE_KEY = "0x" + "1" * 64
# Valid base64 encoded secret for HMAC
API_SECRET_BASE64 = "dGVzdF9zZWNyZXRfa2V5XzEyMzQ1Njc4OTAxMjM0NTY="


@pytest.fixture
def l2_client():
    """Level 2 client with RFQ access"""
    creds = ApiCreds(
        api_key="test_api_key",
        api_secret=API_SECRET_BASE64,
        api_passphrase="test_passphrase",
    )
    return AsyncClobClient(host=HOST, chain_id=CHAIN_ID, key=PRIVATE_KEY, creds=creds)


@pytest.fixture
def rfq_client(l2_client):
    """AsyncRfqClient instance"""
    return l2_client.rfq


class TestAsyncRfqClientInit:
    def test_rfq_client_created_with_parent(self, l2_client):
        """Test that RFQ client is created with parent reference"""
        assert l2_client.rfq is not None
        assert isinstance(l2_client.rfq, AsyncRfqClient)
        assert l2_client.rfq._parent == l2_client


class TestAsyncRfqClientRequests:
    @pytest.mark.asyncio
    async def test_get_rfq_requests(self, rfq_client):
        """Test get_rfq_requests endpoint"""
        expected = {"data": [{"request_id": "req1"}], "next_cursor": "end"}
        with patch(
            "py_clob_client.rfq.async_rfq_client.async_get",
            new_callable=AsyncMock,
            return_value=expected,
        ):
            result = await rfq_client.get_rfq_requests()
            assert result == expected
            assert len(result["data"]) == 1

    @pytest.mark.asyncio
    async def test_get_rfq_requests_with_params(self, rfq_client):
        """Test get_rfq_requests with filter params"""
        params = GetRfqRequestsParams(request_ids=["req1", "req2"])
        expected = {"data": [], "next_cursor": "end"}
        with patch(
            "py_clob_client.rfq.async_rfq_client.async_get",
            new_callable=AsyncMock,
            return_value=expected,
        ) as mock_get:
            result = await rfq_client.get_rfq_requests(params)

            assert result == expected
            # Check that URL contains query params
            call_args = mock_get.call_args[0][0]
            assert "requestIds" in call_args

    @pytest.mark.asyncio
    async def test_cancel_rfq_request(self, rfq_client):
        """Test cancel_rfq_request endpoint"""
        params = CancelRfqRequestParams(request_id="req123")
        with patch(
            "py_clob_client.rfq.async_rfq_client.async_delete",
            new_callable=AsyncMock,
            return_value="OK",
        ):
            result = await rfq_client.cancel_rfq_request(params)
            assert result == "OK"


class TestAsyncRfqClientQuotes:
    @pytest.mark.asyncio
    async def test_get_rfq_requester_quotes(self, rfq_client):
        """Test get_rfq_requester_quotes endpoint"""
        expected = {"data": [{"quote_id": "quote1"}], "next_cursor": "end"}
        with patch(
            "py_clob_client.rfq.async_rfq_client.async_get",
            new_callable=AsyncMock,
            return_value=expected,
        ):
            result = await rfq_client.get_rfq_requester_quotes()
            assert result == expected

    @pytest.mark.asyncio
    async def test_get_rfq_quoter_quotes(self, rfq_client):
        """Test get_rfq_quoter_quotes endpoint"""
        expected = {"data": [{"quote_id": "quote1"}], "next_cursor": "end"}
        with patch(
            "py_clob_client.rfq.async_rfq_client.async_get",
            new_callable=AsyncMock,
            return_value=expected,
        ):
            result = await rfq_client.get_rfq_quoter_quotes()
            assert result == expected

    @pytest.mark.asyncio
    async def test_get_rfq_best_quote(self, rfq_client):
        """Test get_rfq_best_quote endpoint"""
        params = GetRfqBestQuoteParams(request_id="req123")
        expected = {"quote_id": "best_quote", "price": "0.5"}
        with patch(
            "py_clob_client.rfq.async_rfq_client.async_get",
            new_callable=AsyncMock,
            return_value=expected,
        ):
            result = await rfq_client.get_rfq_best_quote(params)
            assert result == expected

    @pytest.mark.asyncio
    async def test_cancel_rfq_quote(self, rfq_client):
        """Test cancel_rfq_quote endpoint"""
        params = CancelRfqQuoteParams(quote_id="quote123")
        with patch(
            "py_clob_client.rfq.async_rfq_client.async_delete",
            new_callable=AsyncMock,
            return_value="OK",
        ):
            result = await rfq_client.cancel_rfq_quote(params)
            assert result == "OK"


class TestAsyncRfqClientConfig:
    @pytest.mark.asyncio
    async def test_rfq_config(self, rfq_client):
        """Test rfq_config endpoint"""
        expected = {
            "min_size": 10,
            "max_size": 10000,
            "quote_ttl_seconds": 300,
        }
        with patch(
            "py_clob_client.rfq.async_rfq_client.async_get",
            new_callable=AsyncMock,
            return_value=expected,
        ):
            result = await rfq_client.rfq_config()
            assert result == expected
            assert result["min_size"] == 10


class TestAsyncRfqClientCreateRequest:
    @pytest.mark.asyncio
    async def test_create_rfq_request(self, rfq_client, l2_client):
        """Test create_rfq_request endpoint"""
        user_request = RfqUserRequest(
            token_id="123456",
            price=0.5,
            side="BUY",
            size=100,
        )

        # Mock the tick size resolution
        with patch.object(
            l2_client,
            "_AsyncClobClient__resolve_tick_size",
            new_callable=AsyncMock,
            return_value="0.01",
        ):
            with patch(
                "py_clob_client.rfq.async_rfq_client.async_post",
                new_callable=AsyncMock,
                return_value={"request_id": "new_req"},
            ) as mock_post:
                result = await rfq_client.create_rfq_request(user_request)

                assert result["request_id"] == "new_req"
                mock_post.assert_called_once()


class TestAsyncRfqClientCreateQuote:
    @pytest.mark.asyncio
    async def test_create_rfq_quote(self, rfq_client, l2_client):
        """Test create_rfq_quote endpoint"""
        user_quote = RfqUserQuote(
            request_id="req123",
            token_id="123456",
            price=0.5,
            side="SELL",
            size=100,
        )

        # Mock the tick size resolution
        with patch.object(
            l2_client,
            "_AsyncClobClient__resolve_tick_size",
            new_callable=AsyncMock,
            return_value="0.01",
        ):
            with patch(
                "py_clob_client.rfq.async_rfq_client.async_post",
                new_callable=AsyncMock,
                return_value={"quote_id": "new_quote"},
            ) as mock_post:
                result = await rfq_client.create_rfq_quote(user_quote)

                assert result["quote_id"] == "new_quote"
                mock_post.assert_called_once()


class TestAsyncRfqClientL2AuthRequired:
    def test_l2_auth_required_for_requests(self):
        """Test that L2 auth is required for RFQ operations"""
        # L1 client (no creds)
        l1_client = AsyncClobClient(host=HOST, chain_id=CHAIN_ID, key=PRIVATE_KEY)

        with pytest.raises(PolyException):
            l1_client.rfq._ensure_l2_auth()

    def test_l2_auth_required_for_quotes(self):
        """Test that L2 auth is required for quote operations"""
        l1_client = AsyncClobClient(host=HOST, chain_id=CHAIN_ID, key=PRIVATE_KEY)

        with pytest.raises(PolyException):
            l1_client.rfq._ensure_l2_auth()
