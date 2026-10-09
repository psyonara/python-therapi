import pytest

from therapi import BaseAPIConsumer

BASE_URL = "https://api.example.test"


@pytest.fixture
def base_url():
    return BASE_URL


@pytest.fixture
def consumer(base_url):
    return BaseAPIConsumer(base_url=base_url)


@pytest.fixture
def consumer_factory(base_url):
    def make(request_modifiers=None, response_modifiers=None, timeout=30.0):
        return BaseAPIConsumer(
            base_url=base_url,
            request_modifiers=request_modifiers,
            response_modifiers=response_modifiers,
            timeout=timeout,
        )

    return make
