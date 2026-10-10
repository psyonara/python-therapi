import logging
from collections.abc import Callable, Collection, Mapping
from typing import Any

from therapi.base import JSONValue, RequestModifier, ResponseModifier

logger = logging.getLogger(__name__)


class UserAgentModifier(RequestModifier):
    """
    Sets a custom User-Agent header.
    """
    def __init__(self, user_agent: str) -> None:
        self.user_agent = user_agent

    def modify_headers(self, headers: dict[str, str]) -> None:
        headers["User-Agent"] = self.user_agent


class LoggingModifier(RequestModifier, ResponseModifier):
    """
    Logs request and response details.

    Sensitive headers listed in ``redact_headers`` are replaced with
    ``<redacted>`` before logging so credentials are not leaked.
    """
    def __init__(
        self,
        log_level: int = logging.DEBUG,
        log_payload: bool = True,
        redact_headers: Collection[str] = ("Authorization", "X-API-Key"),
    ) -> None:
        self.log_level = log_level
        self.log_payload = log_payload
        self.redact_headers = {h.lower() for h in redact_headers}

    def _redacted_headers(self, headers: dict[str, str]) -> dict[str, str]:
        return {
            k: ("<redacted>" if k.lower() in self.redact_headers else v)
            for k, v in headers.items()
        }

    def modify_headers(self, headers: dict[str, str]) -> None:
        logger.log(self.log_level, f"Request headers: {self._redacted_headers(headers)}")

    def modify_params(self, params: dict[str, Any]) -> None:
        logger.log(self.log_level, f"Request params: {params}")

    def modify_response(self, json_data: JSONValue) -> JSONValue:
        if self.log_payload:
            logger.log(self.log_level, f"Response JSON: {json_data}")
        return json_data


class HeaderModifier(RequestModifier):
    """
    Sets arbitrary headers.
    """
    def __init__(self, headers: dict[str, str]) -> None:
        self.extra_headers = headers

    def modify_headers(self, headers: dict[str, str]) -> None:
        headers.update(self.extra_headers)


class PaginationModifier(RequestModifier):
    """
    Adds pagination parameters to the request.
    """
    def __init__(
        self,
        page: int = 1,
        per_page: int = 30,
        page_param: str = "page",
        per_page_param: str = "per_page",
    ) -> None:
        self.page = page
        self.per_page = per_page
        self.page_param = page_param
        self.per_page_param = per_page_param

    def modify_params(self, params: dict[str, Any]) -> None:
        params[self.page_param] = self.page
        params[self.per_page_param] = self.per_page


class ResponseTransformModifier(ResponseModifier):
    """
    Transforms the JSON response into a new dictionary structure based on a mapping.
    The mapping keys represent the new dictionary keys, and values can be:
    - a string: the key to extract from the source JSON.
    - a list/tuple: a path of keys to extract from a nested source JSON.
    - a callable: a function that takes the entire JSON and returns the value.
    """
    def __init__(
        self,
        mapping: Mapping[str, str | list[str] | tuple[str, ...] | Callable[[JSONValue], Any]],
    ) -> None:
        self.mapping = mapping

    def modify_response(self, json_data: JSONValue) -> JSONValue:
        if not isinstance(json_data, dict):
            return json_data

        transformed = {}
        for target_key, source in self.mapping.items():
            if callable(source):
                transformed[target_key] = source(json_data)
            elif isinstance(source, str):
                transformed[target_key] = json_data.get(source)
            elif isinstance(source, (list, tuple)):
                val: JSONValue = json_data
                for k in source:
                    if isinstance(val, dict):
                        val = val.get(k)
                    else:
                        val = None
                        break
                transformed[target_key] = val
        return transformed
