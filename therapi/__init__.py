from dataclasses import dataclass

import requests


@dataclass
class Endpoint:
    url_path: str
    method: str
    required_url_params: list = None


class BaseModifier:
    context: dict = None

    def __init__(self, context: dict):
        self.context = context


class BaseAPIConsumer:
    base_url = None
    request_modifier_classes: list = []
    response_modifier_classes: list = []
    context: dict = {}

    def __init__(self, base_url=None):
        if base_url:
            self.base_url = base_url

        if not self.base_url:
            raise ValueError(
                "A base URL is required. Specify it as a class member, or when initializing your class instance."
            )

    def construct_url(self, *url_parts: str, params: dict = None):
        parts = [self.base_url.strip("/")] + [part.strip("/") for part in url_parts]
        url = "/".join(parts) + "/"

        used_params = []
        for param, value in params.items():
            if f"<{param}>" in url:
                url = url.replace(f"<{param}>", f"{value}")
                used_params.append(param)

        for param in used_params:
            del params[param]

        return url

    def base_request(self, method, path, params=None, payload: dict = None):
        headers = {}
        for request_modifier_class in self.request_modifier_classes:
            request_modifier = request_modifier_class(context=self.context)
            if hasattr(request_modifier, "modify_headers"):
                request_modifier.modify_headers(headers)

        url = self.construct_url(path, params=params)
        print(url, method, params, payload, headers)
        return requests.request(method, url, params=params, json=payload, headers=headers)

    def json_request(self, method: str, path: str, params: dict = None, payload: dict = None):
        response = self.base_request(method, path, params, payload)
        return response.json()

    def call_endpoint(self, endpoint: Endpoint, params: dict = None, payload: dict = None):
        if params is None:
            params = {}
        if endpoint.required_url_params:
            for param in endpoint.required_url_params:
                if param not in params:
                    raise ValueError(f"The URL param '{param}' was not specified.")

        json_response = self.json_request(endpoint.method, endpoint.url_path, params, payload)
        return json_response
