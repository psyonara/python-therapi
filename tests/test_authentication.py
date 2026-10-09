import pytest

from therapi import APIKeyAuthentication, RequestModifier, TokenBearerAuthentication
from therapi.exceptions import AuthenticationError


def test_token_bearer_sets_authorization_header():
    headers = {}
    TokenBearerAuthentication("abc").modify_headers(headers)
    assert headers == {"Authorization": "Bearer abc"}


def test_api_key_sets_default_header():
    headers = {}
    APIKeyAuthentication("k").modify_headers(headers)
    assert headers == {"X-API-Key": "k"}


def test_api_key_custom_header_field():
    headers = {}
    APIKeyAuthentication("k", header_field="X-Token").modify_headers(headers)
    assert headers == {"X-Token": "k"}


@pytest.mark.parametrize(
    "factory",
    [
        lambda: TokenBearerAuthentication(""),
        lambda: TokenBearerAuthentication(None),
        lambda: APIKeyAuthentication(""),
        lambda: APIKeyAuthentication(None),
    ],
)
def test_empty_credentials_raise(factory):
    with pytest.raises(AuthenticationError):
        factory()


def test_authentication_classes_are_request_modifiers():
    assert issubclass(TokenBearerAuthentication, RequestModifier)
    assert issubclass(APIKeyAuthentication, RequestModifier)
