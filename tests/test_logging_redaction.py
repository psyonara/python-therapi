import logging

from therapi import LoggingModifier


def test_redacts_sensitive_headers(caplog):
    modifier = LoggingModifier()
    headers = {"Authorization": "Bearer secret", "X-API-Key": "topsecret", "Accept": "application/json"}

    with caplog.at_level(logging.DEBUG):
        modifier.modify_headers(headers)

    assert "topsecret" not in caplog.text
    assert "Bearer secret" not in caplog.text
    assert "<redacted>" in caplog.text
    assert "application/json" in caplog.text
    # Redaction is logging-only; the live header dict is untouched.
    assert headers["Authorization"] == "Bearer secret"


def test_redaction_is_case_insensitive(caplog):
    modifier = LoggingModifier()

    with caplog.at_level(logging.DEBUG):
        modifier.modify_headers({"authorization": "Bearer z"})

    assert "Bearer z" not in caplog.text


def test_custom_redact_headers(caplog):
    modifier = LoggingModifier(redact_headers=("X-Custom",))

    with caplog.at_level(logging.DEBUG):
        modifier.modify_headers({"X-Custom": "s3cret", "Authorization": "Bearer x"})

    assert "s3cret" not in caplog.text
    assert "Bearer x" in caplog.text


def test_logs_params(caplog):
    modifier = LoggingModifier()

    with caplog.at_level(logging.DEBUG):
        modifier.modify_params({"page": 1})

    assert "page" in caplog.text


def test_logs_response_payload(caplog):
    modifier = LoggingModifier()

    with caplog.at_level(logging.DEBUG):
        result = modifier.modify_response({"a": 1})

    assert result == {"a": 1}
    assert "Response JSON" in caplog.text


def test_response_payload_is_silent_when_disabled(caplog):
    modifier = LoggingModifier(log_payload=False)

    with caplog.at_level(logging.DEBUG):
        modifier.modify_response({"a": 1})

    assert "Response JSON" not in caplog.text
