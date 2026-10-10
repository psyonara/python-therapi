from therapi.base import RequestModifier
from therapi.exceptions import AuthenticationError


class TokenBearerAuthentication(RequestModifier):
    """
    Authenticate a request with Token Bearer Authentication.
    """
    def __init__(self, token: str) -> None:
        if not token:
            raise AuthenticationError("Bearer token must be a non-empty string.")
        self.token = token

    def modify_headers(self, headers: dict[str, str]) -> None:
        headers["Authorization"] = f"Bearer {self.token}"


class APIKeyAuthentication(RequestModifier):
    """
    Authenticate a request with an API Key.
    """
    def __init__(self, api_key: str, header_field: str = "X-API-Key") -> None:
        if not api_key:
            raise AuthenticationError("API key must be a non-empty string.")
        self.api_key = api_key
        self.header_field = header_field

    def modify_headers(self, headers: dict[str, str]) -> None:
        headers[self.header_field] = self.api_key