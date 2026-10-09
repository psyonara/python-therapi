from therapi import BaseAPIConsumer


def test_joins_base_and_parts(consumer):
    assert consumer.construct_url("users", "7") == "https://api.example.test/users/7/"


def test_strips_surrounding_slashes(consumer):
    assert consumer.construct_url("/users/", "/7/") == "https://api.example.test/users/7/"


def test_base_url_only(consumer):
    assert consumer.construct_url() == "https://api.example.test/"


def test_none_params_leave_placeholders_intact(consumer):
    assert consumer.construct_url("things/<thing_id>") == "https://api.example.test/things/<thing_id>/"


def test_substitutes_params(consumer):
    assert consumer.construct_url("things/<thing_id>", params={"thing_id": 7}) == "https://api.example.test/things/7/"


def test_substitutes_placeholder_in_base_url(base_url):
    client = BaseAPIConsumer(base_url=f"{base_url}/<tenant>")
    assert client.construct_url("items", params={"tenant": "acme"}) == "https://api.example.test/acme/items/"


def test_unused_params_are_ignored(consumer):
    assert consumer.construct_url("items", params={"page": 2}) == "https://api.example.test/items/"


def test_does_not_mutate_caller_params(consumer):
    params = {"thing_id": 1, "page": 2}
    consumer.construct_url("things/<thing_id>", params=params)
    assert params == {"thing_id": 1, "page": 2}
