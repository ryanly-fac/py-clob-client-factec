import asyncio
from urllib.parse import urlparse
import httpx

from py_clob_client.clob_types import (
    DropNotificationParams,
    BalanceAllowanceParams,
    OrderScoringParams,
    OrdersScoringParams,
    TradeParams,
    OpenOrderParams,
)

from ..exceptions import PolyApiException

GET = "GET"
POST = "POST"
DELETE = "DELETE"
PUT = "PUT"

def _create_http_client(proxies=None):
    return httpx.Client(http2=True, proxies=proxies)


def _create_async_http_client(proxies=None):
    return httpx.AsyncClient(http2=True, proxies=proxies)


def _proxies_key(proxies) -> str:
    if proxies is None:
        return "default"
    if isinstance(proxies, dict):
        items = tuple(sorted(proxies.items()))
        return f"dict:{items}"
    return f"{proxies}"


def _close_async_client(client: httpx.AsyncClient):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        loop.create_task(client.aclose())
    else:
        try:
            asyncio.run(client.aclose())
        except Exception:
            pass


_sync_clients = {}
_async_clients = {}
_host_proxy_map = {}
_default_proxies = None


def configure_http_clients(*, proxies=None, host: str = None):
    """
    Register proxies (optionally per host) and ensure a reusable client exists.
    """
    global _default_proxies
    if host:
        parsed = urlparse(host)
        host_key = parsed.netloc or host
        _host_proxy_map[host_key] = proxies
    else:
        _default_proxies = proxies

    key = _proxies_key(proxies)

    if key not in _sync_clients:
        _sync_clients[key] = _create_http_client(proxies)

    if key not in _async_clients:
        _async_clients[key] = _create_async_http_client(proxies)


def _get_proxies(endpoint: str, explicit_proxies=None):
    if explicit_proxies is not None:
        return explicit_proxies

    parsed = urlparse(endpoint)
    host = parsed.netloc
    if host in _host_proxy_map:
        return _host_proxy_map[host]

    return _default_proxies


def _get_sync_client(proxies=None):
    key = _proxies_key(proxies)
    client = _sync_clients.get(key)
    if client is None:
        client = _create_http_client(proxies)
        _sync_clients[key] = client
    return client


def _get_async_client(proxies=None):
    key = _proxies_key(proxies)
    client = _async_clients.get(key)
    if client is None:
        client = _create_async_http_client(proxies)
        _async_clients[key] = client
    return client


def overloadHeaders(method: str, headers: dict) -> dict:
    if headers is None:
        headers = dict()
    headers["User-Agent"] = "py_clob_client"

    headers["Accept"] = "*/*"
    headers["Connection"] = "keep-alive"
    headers["Content-Type"] = "application/json"

    if method == GET:
        headers["Accept-Encoding"] = "gzip"

    return headers


def request(endpoint: str, method: str, headers=None, data=None, proxies=None):
    try:
        headers = overloadHeaders(method, headers)
        proxies = _get_proxies(endpoint, proxies)
        client = _get_sync_client(proxies)
        if isinstance(data, str):
            # Pre-serialized body: send exact bytes
            resp = client.request(
                method=method,
                url=endpoint,
                headers=headers,
                content=data.encode("utf-8"),
            )
        else:
            resp = client.request(
                method=method,
                url=endpoint,
                headers=headers,
                json=data,
            )

        if resp.status_code != 200:
            raise PolyApiException(resp)

        try:
            return resp.json()
        except ValueError:
            return resp.text

    except httpx.RequestError:
        raise PolyApiException(error_msg="Request exception!")


def post(endpoint, headers=None, data=None, proxies=None):
    return request(endpoint, POST, headers, data, proxies)


def get(endpoint, headers=None, data=None, proxies=None):
    return request(endpoint, GET, headers, data, proxies)


def delete(endpoint, headers=None, data=None, proxies=None):
    return request(endpoint, DELETE, headers, data, proxies)


def put(endpoint, headers=None, data=None, proxies=None):
    return request(endpoint, PUT, headers, data, proxies)


def build_query_params(url: str, param: str, val: str) -> str:
    url_with_params = url
    last = url_with_params[-1]
    # if last character in url string == "?", append the param directly: api.com?param=value
    if last == "?":
        url_with_params = "{}{}={}".format(url_with_params, param, val)
    else:
        # else add "&", then append the param
        url_with_params = "{}&{}={}".format(url_with_params, param, val)
    return url_with_params


def add_query_trade_params(
    base_url: str, params: TradeParams = None, next_cursor="MA=="
) -> str:
    """
    Adds query parameters to a url
    """
    url = base_url
    # Include `next_cursor` even when `params` is None to advance pagination.
    has_query = bool(next_cursor) or (
        bool(params)
        and any(
            [
                params.market,
                params.asset_id,
                params.after,
                params.before,
                params.maker_address,
                params.id,
            ]
        )
    )
    if has_query:
        url = url + "?"
    if params:
        if params.market:
            url = build_query_params(url, "market", params.market)
        if params.asset_id:
            url = build_query_params(url, "asset_id", params.asset_id)
        if params.after:
            url = build_query_params(url, "after", params.after)
        if params.before:
            url = build_query_params(url, "before", params.before)
        if params.maker_address:
            url = build_query_params(url, "maker_address", params.maker_address)
        if params.id:
            url = build_query_params(url, "id", params.id)
    if next_cursor:
        url = build_query_params(url, "next_cursor", next_cursor)
    return url


def add_query_open_orders_params(
    base_url: str, params: OpenOrderParams = None, next_cursor="MA=="
) -> str:
    """
    Adds query parameters to a url
    """
    url = base_url
    # Include `next_cursor` even when `params` is None to advance pagination.
    has_query = bool(next_cursor) or (
        bool(params) and any([params.market, params.asset_id, params.id])
    )
    if has_query:
        url = url + "?"
    if params:
        if params.market:
            url = build_query_params(url, "market", params.market)
        if params.asset_id:
            url = build_query_params(url, "asset_id", params.asset_id)
        if params.id:
            url = build_query_params(url, "id", params.id)
    if next_cursor:
        url = build_query_params(url, "next_cursor", next_cursor)
    return url


def drop_notifications_query_params(
    base_url: str, params: DropNotificationParams = None
) -> str:
    """
    Adds query parameters to a url
    """
    url = base_url
    if params:
        url = url + "?"
        if params.ids:
            url = build_query_params(url, "ids", ",".join(params.ids))
    return url


def add_balance_allowance_params_to_url(
    base_url: str, params: BalanceAllowanceParams = None
) -> str:
    """
    Adds query parameters to a url
    """
    url = base_url
    if params:
        url = url + "?"
        if params.asset_type:
            url = build_query_params(url, "asset_type", params.asset_type.__str__())
        if params.token_id:
            url = build_query_params(url, "token_id", params.token_id)
        if params.signature_type is not None:
            url = build_query_params(url, "signature_type", params.signature_type)
    return url


def add_order_scoring_params_to_url(
    base_url: str, params: OrderScoringParams = None
) -> str:
    """
    Adds query parameters to a url
    """
    url = base_url
    if params:
        url = url + "?"
        if params.orderId:
            url = build_query_params(url, "order_id", params.orderId)
    return url


def add_orders_scoring_params_to_url(
    base_url: str, params: OrdersScoringParams = None
) -> str:
    """
    Adds query parameters to a url
    """
    url = base_url
    if params:
        url = url + "?"
        if params.orderIds:
            url = build_query_params(url, "order_ids", ",".join(params.orderIds))
    return url


# =============================================================================
# Async HTTP Functions
# =============================================================================


async def async_request(endpoint: str, method: str, headers=None, data=None, proxies=None):
    """Async version of request"""
    try:
        headers = overloadHeaders(method, headers)
        proxies = _get_proxies(endpoint, proxies)
        client = _get_async_client(proxies)
        if isinstance(data, str):
            # Pre-serialized body: send exact bytes
            resp = await client.request(
                method=method,
                url=endpoint,
                headers=headers,
                content=data.encode("utf-8"),
            )
        else:
            resp = await client.request(
                method=method,
                url=endpoint,
                headers=headers,
                json=data,
            )

        if resp.status_code != 200:
            raise PolyApiException(resp)

        try:
            return resp.json()
        except ValueError:
            return resp.text

    except httpx.RequestError:
        raise PolyApiException(error_msg="Request exception!")


async def async_post(endpoint, headers=None, data=None, proxies=None):
    return await async_request(endpoint, POST, headers, data, proxies)


async def async_get(endpoint, headers=None, data=None, proxies=None):
    return await async_request(endpoint, GET, headers, data, proxies)


async def async_delete(endpoint, headers=None, data=None, proxies=None):
    return await async_request(endpoint, DELETE, headers, data, proxies)


async def async_put(endpoint, headers=None, data=None, proxies=None):
    return await async_request(endpoint, PUT, headers, data, proxies)
