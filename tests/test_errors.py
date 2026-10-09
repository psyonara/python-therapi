import httpx
import pytest

from therapi import APIKeyAuthentication, Endpoint, TokenBearerAuthentication
from therapi.exceptions import AuthenticationError


@pytest.mark.parametrize("status", [404, 500])
def test_http_status_error(consumer, respx_mock, base_url, status):
    respx_mock.get(f"{base_url}/items/").mock(return_value=httpx.Response(status, json={"error": "x"}))

    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        consumer.json_request("GET", "items")

    assert exc_info.value.response.status_code == status
    assert exc_info.value.request is not None


def test_timeout_propagates(consumer, respx_mock, base_url):
    respx_mock.get(f"{base_url}/items/").mock(side_effect=httpx.TimeoutException("timed out"))

    with pytest.raises(httpx.TimeoutException):
        consumer.json_request("GET", "items")


def test_missing_required_url_param_raises_value_error(consumer):
    endpoint = Endpoint(url_path="/things/<thing_id>/", method="GET", required_url_params=["thing_id"])

    with pytest.raises(ValueError):
        consumer.call_endpoint(endpoint)


def test_authentication_error_propagates():
    with pytest.raises(AuthenticationError):
        TokenBearerAuthentication("")
    with pytest.raises(AuthenticationError):
        APIKeyAuthentication("")
