from therapi import BaseModifier
from therapi.exceptions import AuthenticationError


class TokenBearerAuthentication(BaseModifier):
    """
    Authenticate a request with Token Bearer Authentication.
    """
    def modify_headers(self, headers: dict):
        if "bearer_token" not in self.context:
            raise AuthenticationError("Bearer Token not found in context")

        headers["Authorization"] = f"Bearer {self.context.get('bearer_token')}"
