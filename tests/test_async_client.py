import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from py_clob_client.async_client import AsyncClobClient
from py_clob_client.clob_types import ApiCreds, OrderArgs, BookParams
from py_clob_client.constants import L0, L1, L2
from py_clob_client.exceptions import PolyException


# Test constants
HOST = "https://clob.polymarket.com"
CHAIN_ID = 137
PRIVATE_KEY = "0x" + "1" * 64  # Dummy private key
# Valid base64 encoded secret for HMAC
API_SECRET_BASE64 = "dGVzdF9zZWNyZXRfa2V5XzEyMzQ1Njc4OTAxMjM0NTY="


@pytest.fixture
def l0_client():
    """Level 0 client - no auth"""
    return AsyncClobClient(host=HOST)


@pytest.fixture
def l1_client():
    """Level 1 client - with signer"""
    return AsyncClobClient(host=HOST, chain_id=CHAIN_ID, key=PRIVATE_KEY)


@pytest.fixture
def l2_client():
    """Level 2 client - with signer and creds"""
    creds = ApiCreds(
        api_key="test_api_key",
        api_secret=API_SECRET_BASE64,
        api_passphrase="test_passphrase",
    )
    return AsyncClobClient(host=HOST, chain_id=CHAIN_ID, key=PRIVATE_KEY, creds=creds)


class TestAsyncClobClientInit:
    def test_init_level_0(self, l0_client):
        """Test L0 client initialization"""
        assert l0_client.host == HOST
        assert l0_client.mode == L0
        assert l0_client.signer is None
        assert l0_client.creds is None

    def test_init_level_1(self, l1_client):
        """Test L1 client initialization"""
        assert l1_client.host == HOST
        assert l1_client.mode == L1
        assert l1_client.signer is not None
        assert l1_client.creds is None

    def test_init_level_2(self, l2_client):
        """Test L2 client initialization"""
        assert l2_client.host == HOST
        assert l2_client.mode == L2
        assert l2_client.signer is not None
        assert l2_client.creds is not None

    def test_host_trailing_slash_removed(self):
        """Test that trailing slash is removed from host"""
        client = AsyncClobClient(host="https://example.com/")
        assert client.host == "https://example.com"


class TestAsyncClobClientPublicEndpoints:
    @pytest.mark.asyncio
    async def test_get_ok(self, l0_client):
        """Test get_ok endpoint"""
        with patch(
            "py_clob_client.async_client.async_get",
            new_callable=AsyncMock,
            return_value="OK",
        ) as mock_get:
            result = await l0_client.get_ok()

            assert result == "OK"
            mock_get.assert_called_once_with(f"{HOST}/")

    @pytest.mark.asyncio
    async def test_get_server_time(self, l0_client):
        """Test get_server_time endpoint"""
        expected = {"timestamp": 1234567890}
        with patch(
            "py_clob_client.async_client.async_get",
            new_callable=AsyncMock,
            return_value=expected,
        ) as mock_get:
            result = await l0_client.get_server_time()

            assert result == expected

    @pytest.mark.asyncio
    async def test_get_midpoint(self, l0_client):
        """Test get_midpoint endpoint"""
        token_id = "12345"
        expected = {"mid": "0.5"}
        with patch(
            "py_clob_client.async_client.async_get",
            new_callable=AsyncMock,
            return_value=expected,
        ):
            result = await l0_client.get_midpoint(token_id)
            assert result == expected

    @pytest.mark.asyncio
    async def test_get_price(self, l0_client):
        """Test get_price endpoint"""
        token_id = "12345"
        side = "BUY"
        expected = {"price": "0.45"}
        with patch(
            "py_clob_client.async_client.async_get",
            new_callable=AsyncMock,
            return_value=expected,
        ):
            result = await l0_client.get_price(token_id, side)
            assert result == expected

    @pytest.mark.asyncio
    async def test_get_spread(self, l0_client):
        """Test get_spread endpoint"""
        token_id = "12345"
        expected = {"spread": "0.02"}
        with patch(
            "py_clob_client.async_client.async_get",
            new_callable=AsyncMock,
            return_value=expected,
        ):
            result = await l0_client.get_spread(token_id)
            assert result == expected

    @pytest.mark.asyncio
    async def test_get_order_book(self, l0_client):
        """Test get_order_book endpoint"""
        token_id = "12345"
        raw_response = {
            "market": "test",
            "asset_id": token_id,
            "bids": [{"price": "0.45", "size": "100"}],
            "asks": [{"price": "0.55", "size": "100"}],
            "hash": "abc123",
            "timestamp": "1234567890",
            "last_trade_price": "0.50",
            "min_order_size": "5",
            "neg_risk": False,
            "tick_size": "0.01",
        }
        with patch(
            "py_clob_client.async_client.async_get",
            new_callable=AsyncMock,
            return_value=raw_response,
        ):
            result = await l0_client.get_order_book(token_id)
            assert result is not None
            assert result.bids is not None
            assert result.asks is not None

    @pytest.mark.asyncio
    async def test_get_markets(self, l0_client):
        """Test get_markets endpoint"""
        expected = {"data": [], "next_cursor": "end"}
        with patch(
            "py_clob_client.async_client.async_get",
            new_callable=AsyncMock,
            return_value=expected,
        ):
            result = await l0_client.get_markets()
            assert result == expected


class TestAsyncClobClientL1Endpoints:
    @pytest.mark.asyncio
    async def test_create_api_key(self, l1_client):
        """Test create_api_key endpoint"""
        expected_response = {
            "apiKey": "new_key",
            "secret": "new_secret",
            "passphrase": "new_passphrase",
        }
        with patch(
            "py_clob_client.async_client.async_post",
            new_callable=AsyncMock,
            return_value=expected_response,
        ):
            result = await l1_client.create_api_key()

            assert result is not None
            assert result.api_key == "new_key"
            assert result.api_secret == "new_secret"
            assert result.api_passphrase == "new_passphrase"

    def test_create_api_key_requires_l1_auth(self, l0_client):
        """Test that create_api_key requires L1 auth"""
        with pytest.raises(PolyException):
            l0_client.assert_level_1_auth()

    @pytest.mark.asyncio
    async def test_derive_api_key(self, l1_client):
        """Test derive_api_key endpoint"""
        expected_response = {
            "apiKey": "derived_key",
            "secret": "derived_secret",
            "passphrase": "derived_passphrase",
        }
        with patch(
            "py_clob_client.async_client.async_get",
            new_callable=AsyncMock,
            return_value=expected_response,
        ):
            result = await l1_client.derive_api_key()

            assert result is not None
            assert result.api_key == "derived_key"


class TestAsyncClobClientL2Endpoints:
    @pytest.mark.asyncio
    async def test_get_orders(self, l2_client):
        """Test get_orders endpoint"""
        response = {"data": [{"id": "order1"}], "next_cursor": "LTE="}
        with patch(
            "py_clob_client.async_client.async_get",
            new_callable=AsyncMock,
            return_value=response,
        ):
            result = await l2_client.get_orders()
            assert len(result) == 1
            assert result[0]["id"] == "order1"

    def test_get_orders_requires_l2_auth(self, l1_client):
        """Test that get_orders requires L2 auth"""
        with pytest.raises(PolyException):
            l1_client.assert_level_2_auth()

    @pytest.mark.asyncio
    async def test_get_trades(self, l2_client):
        """Test get_trades endpoint"""
        response = {"data": [{"id": "trade1"}], "next_cursor": "LTE="}
        with patch(
            "py_clob_client.async_client.async_get",
            new_callable=AsyncMock,
            return_value=response,
        ):
            result = await l2_client.get_trades()
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_cancel(self, l2_client):
        """Test cancel endpoint"""
        with patch(
            "py_clob_client.async_client.async_delete",
            new_callable=AsyncMock,
            return_value={"success": True},
        ):
            result = await l2_client.cancel("order123")
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_cancel_all(self, l2_client):
        """Test cancel_all endpoint"""
        with patch(
            "py_clob_client.async_client.async_delete",
            new_callable=AsyncMock,
            return_value={"canceled": 5},
        ):
            result = await l2_client.cancel_all()
            assert result["canceled"] == 5

    @pytest.mark.asyncio
    async def test_get_api_keys(self, l2_client):
        """Test get_api_keys endpoint"""
        expected = [{"key": "key1"}, {"key": "key2"}]
        with patch(
            "py_clob_client.async_client.async_get",
            new_callable=AsyncMock,
            return_value=expected,
        ):
            result = await l2_client.get_api_keys()
            assert len(result) == 2


class TestAsyncClobClientBatchEndpoints:
    @pytest.mark.asyncio
    async def test_get_midpoints(self, l0_client):
        """Test get_midpoints batch endpoint"""
        params = [BookParams(token_id="123"), BookParams(token_id="456")]
        expected = [{"mid": "0.5"}, {"mid": "0.6"}]
        with patch(
            "py_clob_client.async_client.async_post",
            new_callable=AsyncMock,
            return_value=expected,
        ):
            result = await l0_client.get_midpoints(params)
            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_prices(self, l0_client):
        """Test get_prices batch endpoint"""
        params = [
            BookParams(token_id="123", side="BUY"),
            BookParams(token_id="456", side="SELL"),
        ]
        expected = [{"price": "0.45"}, {"price": "0.55"}]
        with patch(
            "py_clob_client.async_client.async_post",
            new_callable=AsyncMock,
            return_value=expected,
        ):
            result = await l0_client.get_prices(params)
            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_order_books(self, l0_client):
        """Test get_order_books batch endpoint"""
        params = [BookParams(token_id="123"), BookParams(token_id="456")]
        raw_response = [
            {
                "market": "test1",
                "asset_id": "123",
                "bids": [],
                "asks": [],
                "hash": "abc",
                "timestamp": "1234567890",
                "last_trade_price": "0.50",
                "min_order_size": "5",
                "neg_risk": False,
                "tick_size": "0.01",
            },
            {
                "market": "test2",
                "asset_id": "456",
                "bids": [],
                "asks": [],
                "hash": "def",
                "timestamp": "1234567890",
                "last_trade_price": "0.60",
                "min_order_size": "5",
                "neg_risk": False,
                "tick_size": "0.01",
            },
        ]
        with patch(
            "py_clob_client.async_client.async_post",
            new_callable=AsyncMock,
            return_value=raw_response,
        ):
            result = await l0_client.get_order_books(params)
            assert len(result) == 2


class TestAsyncClobClientCaching:
    @pytest.mark.asyncio
    async def test_get_tick_size_caches_result(self, l0_client):
        """Test that get_tick_size caches the result"""
        token_id = "12345"
        response = {"minimum_tick_size": 0.01}

        with patch(
            "py_clob_client.async_client.async_get",
            new_callable=AsyncMock,
            return_value=response,
        ) as mock_get:
            # First call
            result1 = await l0_client.get_tick_size(token_id)
            # Second call - should use cache
            result2 = await l0_client.get_tick_size(token_id)

            assert result1 == "0.01"
            assert result2 == "0.01"
            # Should only be called once due to caching
            assert mock_get.call_count == 1

    @pytest.mark.asyncio
    async def test_get_neg_risk_caches_result(self, l0_client):
        """Test that get_neg_risk caches the result"""
        token_id = "12345"
        response = {"neg_risk": True}

        with patch(
            "py_clob_client.async_client.async_get",
            new_callable=AsyncMock,
            return_value=response,
        ) as mock_get:
            result1 = await l0_client.get_neg_risk(token_id)
            result2 = await l0_client.get_neg_risk(token_id)

            assert result1 is True
            assert result2 is True
            assert mock_get.call_count == 1
