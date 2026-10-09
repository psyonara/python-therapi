from dataclasses import dataclass

import httpx


@dataclass
class Endpoint:
    url_path: str
    method: str
    required_url_params: list = None


class RequestModifier:
    def modify_headers(self, headers: dict):
        pass

    def modify_params(self, params: dict):
        pass


class ResponseModifier:
    def modify_response(self, json_data):
        return json_data


class BaseAPIConsumer:
    base_url = None
    request_modifiers: list = None
    response_modifiers: list = None

    def __init__(self, base_url=None, request_modifiers=None, response_modifiers=None, timeout=30.0):
        if base_url:
            self.base_url = base_url

        self.request_modifiers = request_modifiers if request_modifiers is not None else []
        self.response_modifiers = response_modifiers if response_modifiers is not None else []
        self.timeout = timeout

        if not self.base_url:
            raise ValueError(
                "A base URL is required. Specify it as a class member, or when initializing your class instance."
            )

    def _build_url(self, *url_parts: str, params: dict = None):
        parts = [self.base_url.strip("/")] + [part.strip("/") for part in url_parts]
        url = "/".join(parts) + "/"

        remaining_params = dict(params or {})
        for param, value in list(remaining_params.items()):
            if f"<{param}>" in url:
                url = url.replace(f"<{param}>", f"{value}")
                del remaining_params[param]

        return url, remaining_params

    def construct_url(self, *url_parts: str, params: dict = None):
        return self._build_url(*url_parts, params=params)[0]

    def json_request(self, method, path, params=None, payload: dict = None):
        headers = {}
        params = dict(params or {})
        for modifier in self.request_modifiers:
            modifier.modify_headers(headers)
            modifier.modify_params(params)

        url, query_params = self._build_url(path, params=params)
        response = httpx.request(
            method,
            url,
            params=query_params,
            json=payload,
            headers=headers,
            timeout=self.timeout,
            follow_redirects=True,
        )
        response.raise_for_status()

        json_data = response.json()

        for modifier in self.response_modifiers:
            json_data = modifier.modify_response(json_data)

        return json_data

    def call_endpoint(self, endpoint: Endpoint, params: dict = None, payload: dict = None):
        params = dict(params or {})
        if endpoint.required_url_params:
            for param in endpoint.required_url_params:
                if param not in params:
                    raise ValueError(f"The URL param '{param}' was not specified.")

        json_response = self.json_request(endpoint.method, endpoint.url_path, params, payload)
        return json_response