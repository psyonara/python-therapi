import httpx
import pytest

from therapi import Endpoint


def test_required_url_param_is_substituted(consumer, respx_mock, base_url):
    route = respx_mock.get(f"{base_url}/things/5/").mock(return_value=httpx.Response(200, json={"id": 5}))
    endpoint = Endpoint(url_path="/things/<thing_id>/", method="GET", required_url_params=["thing_id"])

    assert consumer.call_endpoint(endpoint, params={"thing_id": 5}) == {"id": 5}
    assert len(route.calls.last.request.url.params) == 0


def test_missing_required_url_param_raises(consumer):
    endpoint = Endpoint(url_path="/things/<thing_id>/", method="GET", required_url_params=["thing_id"])

    with pytest.raises(ValueError, match="The URL param 'thing_id' was not specified."):
        consumer.call_endpoint(endpoint, params={})


def test_endpoint_without_required_params(consumer, respx_mock, base_url):
    respx_mock.get(f"{base_url}/items/").mock(return_value=httpx.Response(200, json=[]))
    endpoint = Endpoint(url_path="/items/", method="GET")

    assert consumer.call_endpoint(endpoint) == []


def test_query_params_and_payload_are_forwarded(consumer, respx_mock, base_url):
    route = respx_mock.post(f"{base_url}/collections/").mock(return_value=httpx.Response(201, json={"id": 1}))
    endpoint = Endpoint(url_path="/collections/", method="POST")

    result = consumer.call_endpoint(endpoint, params={"page": 2}, payload={"name": "things"})

    assert result == {"id": 1}
    request = route.calls.last.request
    assert request.url.params["page"] == "2"
    assert request.read() == b'{"name":"things"}'


def test_does_not_mutate_caller_params(consumer, respx_mock, base_url):
    respx_mock.get(f"{base_url}/things/5/").mock(return_value=httpx.Response(200, json={}))
    endpoint = Endpoint(url_path="/things/<thing_id>/", method="GET", required_url_params=["thing_id"])
    params = {"thing_id": 5, "page": 2}

    consumer.call_endpoint(endpoint, params=params)

    assert params == {"thing_id": 5, "page": 2}
