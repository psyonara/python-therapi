import json
from unittest import mock

import httpx
import pytest

from therapi import BaseAPIConsumer, ResponseModifier


class _ClassLevelConsumer(BaseAPIConsumer):
    base_url = "https://class.example.test"


def test_class_level_base_url_is_used():
    assert _ClassLevelConsumer().base_url == "https://class.example.test"


def test_missing_base_url_raises():
    with pytest.raises(ValueError, match="A base URL is required"):
        BaseAPIConsumer()


class _CountingModifier(ResponseModifier):
    def __init__(self, key):
        self.key = key

    def modify_response(self, json_data):
        json_data[self.key] = json_data.get(self.key, 0) + 1
        return json_data


def test_get_with_query_params(consumer, respx_mock, base_url):
    route = respx_mock.get(f"{base_url}/items/").mock(return_value=httpx.Response(200, json={"data": []}))

    result = consumer.json_request("GET", "items", params={"page": 2, "per_page": 10})

    assert result == {"data": []}
    request = route.calls.last.request
    assert request.url.params["page"] == "2"
    assert request.url.params["per_page"] == "10"


def test_path_params_are_not_leaked_into_query(consumer, respx_mock, base_url):
    route = respx_mock.get(f"{base_url}/users/7/items/").mock(return_value=httpx.Response(200, json={"ok": True}))

    consumer.json_request("GET", "users/<user_id>/items", params={"user_id": 7, "page": 2})

    request = route.calls.last.request
    assert request.url.path == "/users/7/items/"
    assert request.url.params["page"] == "2"
    assert "user_id" not in request.url.params


def test_placeholder_only_params_produce_no_query(consumer, respx_mock, base_url):
    route = respx_mock.get(f"{base_url}/things/9/").mock(return_value=httpx.Response(200, json={}))

    consumer.json_request("GET", "things/<thing_id>", params={"thing_id": 9})

    assert route.calls.last.request.url.query == b""


def test_transport_contract(consumer):
    fake_response = mock.Mock()
    fake_response.json.return_value = {"ok": True}

    with mock.patch("therapi.base.httpx.request", return_value=fake_response) as request:
        consumer.json_request("POST", "items", params={"q": "x"}, payload={"a": 1})

    args, kwargs = request.call_args
    assert args[0] == "POST"
    assert args[1] == "https://api.example.test/items/"
    assert kwargs["params"] == {"q": "x"}
    assert kwargs["json"] == {"a": 1}
    assert kwargs["headers"] == {}
    assert kwargs["timeout"] == 30.0
    assert kwargs["follow_redirects"] is True
    fake_response.raise_for_status.assert_called_once()


def test_custom_timeout_is_passed(base_url):
    client = BaseAPIConsumer(base_url=base_url, timeout=5.0)
    fake_response = mock.Mock()
    fake_response.json.return_value = {}

    with mock.patch("therapi.base.httpx.request", return_value=fake_response) as request:
        client.json_request("GET", "items")

    assert request.call_args.kwargs["timeout"] == 5.0


def test_response_modifiers_apply_in_order(consumer_factory, respx_mock, base_url):
    respx_mock.get(f"{base_url}/items/").mock(return_value=httpx.Response(200, json={}))

    client = consumer_factory(response_modifiers=[_CountingModifier("a"), _CountingModifier("b"), _CountingModifier("a")])

    assert client.json_request("GET", "items") == {"a": 2, "b": 1}


def test_follows_redirects(consumer, respx_mock, base_url):
    respx_mock.get(f"{base_url}/old/").mock(
        return_value=httpx.Response(302, headers={"Location": f"{base_url}/new/"})
    )
    respx_mock.get(f"{base_url}/new/").mock(return_value=httpx.Response(200, json={"moved": True}))

    assert consumer.json_request("GET", "old") == {"moved": True}


def test_post_payload_is_sent_as_json(consumer, respx_mock, base_url):
    route = respx_mock.post(f"{base_url}/items/").mock(return_value=httpx.Response(201, json={"id": 1}))

    result = consumer.json_request("POST", "items", payload={"name": "widget"})

    assert result == {"id": 1}
    request = route.calls.last.request
    assert request.headers["content-type"] == "application/json"
    assert json.loads(request.content) == {"name": "widget"}
