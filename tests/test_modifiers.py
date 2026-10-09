import httpx

from therapi import (
    BaseAPIConsumer,
    HeaderModifier,
    PaginationModifier,
    ResponseModifier,
    ResponseTransformModifier,
    UserAgentModifier,
)


def test_user_agent_modifier_sets_header():
    headers = {}
    UserAgentModifier("therapi/1").modify_headers(headers)
    assert headers["User-Agent"] == "therapi/1"


def test_header_modifier_merges_headers():
    headers = {"Accept": "application/json"}
    HeaderModifier({"X-Trace": "t"}).modify_headers(headers)
    assert headers == {"Accept": "application/json", "X-Trace": "t"}


def test_pagination_modifier_defaults():
    params = {}
    PaginationModifier().modify_params(params)
    assert params == {"page": 1, "per_page": 30}


def test_pagination_modifier_custom_names():
    params = {}
    PaginationModifier(page=3, per_page=5, page_param="p", per_page_param="n").modify_params(params)
    assert params == {"p": 3, "n": 5}


def test_transform_string_source():
    modifier = ResponseTransformModifier({"id": "thing_id"})
    assert modifier.modify_response({"thing_id": 1}) == {"id": 1}


def test_transform_nested_path_source():
    modifier = ResponseTransformModifier({"x": ["a", "b", "c"]})
    assert modifier.modify_response({"a": {"b": {"c": 5}}}) == {"x": 5}


def test_transform_missing_nested_path_is_none():
    modifier = ResponseTransformModifier({"x": ["a", "missing"]})
    assert modifier.modify_response({"a": {}}) == {"x": None}


def test_transform_path_through_non_dict_is_none():
    modifier = ResponseTransformModifier({"x": ["a", "b"]})
    assert modifier.modify_response({"a": 5}) == {"x": None}


def test_transform_callable_source():
    modifier = ResponseTransformModifier({"count": len})
    assert modifier.modify_response({"a": 1, "b": 2}) == {"count": 2}


def test_transform_missing_string_source_is_none():
    modifier = ResponseTransformModifier({"x": "nope"})
    assert modifier.modify_response({}) == {"x": None}


def test_transform_non_dict_passthrough():
    modifier = ResponseTransformModifier({"x": "y"})
    assert modifier.modify_response([1, 2]) == [1, 2]


def test_base_response_modifier_is_identity():
    assert ResponseModifier().modify_response({"a": 1}) == {"a": 1}


def test_modifiers_apply_to_real_request(respx_mock, base_url):
    route = respx_mock.get(f"{base_url}/items/").mock(return_value=httpx.Response(200, json={}))
    client = BaseAPIConsumer(
        base_url=base_url,
        request_modifiers=[HeaderModifier({"X-Trace": "t"}), PaginationModifier()],
    )

    client.json_request("GET", "items")

    request = route.calls.last.request
    assert request.headers["X-Trace"] == "t"
    assert request.url.params["page"] == "1"
    assert request.url.params["per_page"] == "30"
