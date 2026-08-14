"""Tests de AnthropicProvider (V0.7).

Ninguno hace una llamada de red real: ``urllib.request.urlopen`` se mockea en
todos los casos (ver seccion 10 de
prompts/V0.7—LLM-REAL-PROVIDER-&-AI-FOUNDATION.md). Las credenciales usadas son
siempre ficticias.
"""

from __future__ import annotations

import io
import json
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from providers import (
    AnthropicProvider,
    InvalidModelError,
    InvalidResponseError,
    MissingCredentialError,
    ProviderConfig,
    ProviderRequestError,
    ProviderTimeoutError,
    get_provider,
)

FAKE_API_KEY = "sk-ant-fake-test-key-never-real"
FAKE_MODEL = "claude-test-model"


def _config(**overrides) -> ProviderConfig:
    values = {"provider": "anthropic", "model": FAKE_MODEL, "api_key": FAKE_API_KEY}
    values.update(overrides)
    return ProviderConfig(**values)


def _success_response(text: str = "hello from anthropic") -> MagicMock:
    body = json.dumps(
        {
            "content": [{"type": "text", "text": text}],
            "model": FAKE_MODEL,
            "role": "assistant",
            "stop_reason": "end_turn",
        }
    ).encode("utf-8")
    response = MagicMock()
    response.read.return_value = body
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    return response


def _http_error(code: int, body: dict | bytes) -> urllib.error.HTTPError:
    body_bytes = body if isinstance(body, bytes) else json.dumps(body).encode("utf-8")
    return urllib.error.HTTPError(
        url="https://api.anthropic.com/v1/messages",
        code=code,
        msg="error",
        hdrs=None,
        fp=io.BytesIO(body_bytes),
    )


# 1. construccion correcta
def test_construction_with_valid_config_succeeds():
    AnthropicProvider(_config())


# 2. ausencia de API key
def test_missing_api_key_raises_missing_credential_error():
    with pytest.raises(MissingCredentialError):
        AnthropicProvider(_config(api_key=None))


# 3. ausencia de modelo cuando es obligatorio
def test_missing_model_raises_invalid_model_error():
    with pytest.raises(InvalidModelError):
        AnthropicProvider(_config(model=None))


# 4 y 6. construccion del request y payload correcto
@patch("providers.anthropic.urllib.request.urlopen")
def test_request_and_payload_are_built_correctly(mock_urlopen):
    mock_urlopen.return_value = _success_response()
    provider = AnthropicProvider(_config())

    provider.generate("hola mundo")

    request = mock_urlopen.call_args.args[0]
    assert request.full_url == "https://api.anthropic.com/v1/messages"
    assert request.get_method() == "POST"

    payload = json.loads(request.data)
    assert payload["model"] == FAKE_MODEL
    assert payload["messages"] == [{"role": "user", "content": "hola mundo"}]
    assert isinstance(payload["max_tokens"], int) and payload["max_tokens"] > 0


# 5. headers correctos
@patch("providers.anthropic.urllib.request.urlopen")
def test_headers_are_correct(mock_urlopen):
    mock_urlopen.return_value = _success_response()
    provider = AnthropicProvider(_config())

    provider.generate("hola")

    request = mock_urlopen.call_args.args[0]
    assert request.get_header("X-api-key") == FAKE_API_KEY
    assert request.get_header("Anthropic-version")
    assert request.get_header("Content-type") == "application/json"


# 7. parseo de respuesta valida
@patch("providers.anthropic.urllib.request.urlopen")
def test_valid_response_is_parsed_to_text(mock_urlopen):
    mock_urlopen.return_value = _success_response("respuesta esperada")
    provider = AnthropicProvider(_config())

    result = provider.generate("hola")

    assert result == "respuesta esperada"


@patch("providers.anthropic.urllib.request.urlopen")
def test_multiple_text_blocks_are_concatenated(mock_urlopen):
    body = json.dumps({"content": [{"type": "text", "text": "a"}, {"type": "text", "text": "b"}]}).encode()
    response = MagicMock()
    response.read.return_value = body
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    mock_urlopen.return_value = response

    provider = AnthropicProvider(_config())
    assert provider.generate("hola") == "ab"


# 8. respuesta sin contenido esperado
@patch("providers.anthropic.urllib.request.urlopen")
def test_response_without_expected_content_raises_invalid_response_error(mock_urlopen):
    body = json.dumps({"content": []}).encode("utf-8")
    response = MagicMock()
    response.read.return_value = body
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    mock_urlopen.return_value = response

    provider = AnthropicProvider(_config())
    with pytest.raises(InvalidResponseError):
        provider.generate("hola")


@patch("providers.anthropic.urllib.request.urlopen")
def test_response_with_only_non_text_blocks_raises_invalid_response_error(mock_urlopen):
    body = json.dumps({"content": [{"type": "tool_use", "id": "x"}]}).encode("utf-8")
    response = MagicMock()
    response.read.return_value = body
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    mock_urlopen.return_value = response

    provider = AnthropicProvider(_config())
    with pytest.raises(InvalidResponseError):
        provider.generate("hola")


# 9. JSON invalido
@patch("providers.anthropic.urllib.request.urlopen")
def test_invalid_json_raises_invalid_response_error(mock_urlopen):
    response = MagicMock()
    response.read.return_value = b"not json at all"
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    mock_urlopen.return_value = response

    provider = AnthropicProvider(_config())
    with pytest.raises(InvalidResponseError):
        provider.generate("hola")


# 10. timeout
@patch("providers.anthropic.urllib.request.urlopen")
def test_timeout_raises_provider_timeout_error(mock_urlopen):
    mock_urlopen.side_effect = TimeoutError("timed out")
    provider = AnthropicProvider(_config())

    with pytest.raises(ProviderTimeoutError):
        provider.generate("hola")


@patch("providers.anthropic.urllib.request.urlopen")
def test_connect_phase_timeout_wrapped_in_urlerror_is_still_provider_timeout_error(mock_urlopen):
    """Regresion: un timeout durante la conexion/envio de la request (a
    diferencia de uno durante la lectura de la respuesta) llega envuelto por
    urllib como URLError(reason=TimeoutError(...)), no como TimeoutError
    directo -- debia clasificarse igual como ProviderTimeoutError, no como
    ProviderRequestError. Ver providers/anthropic.py."""
    mock_urlopen.side_effect = urllib.error.URLError(TimeoutError("timed out"))
    provider = AnthropicProvider(_config())

    with pytest.raises(ProviderTimeoutError):
        provider.generate("hola")


# 11. HTTP 4xx
@patch("providers.anthropic.urllib.request.urlopen")
def test_http_4xx_raises_provider_request_error(mock_urlopen):
    mock_urlopen.side_effect = _http_error(
        400, {"type": "error", "error": {"type": "invalid_request_error", "message": "bad request"}}
    )
    provider = AnthropicProvider(_config())

    with pytest.raises(ProviderRequestError, match="400"):
        provider.generate("hola")


# 12. HTTP 5xx
@patch("providers.anthropic.urllib.request.urlopen")
def test_http_5xx_raises_provider_request_error(mock_urlopen):
    mock_urlopen.side_effect = _http_error(500, {"type": "error", "error": {"message": "server error"}})
    provider = AnthropicProvider(_config())

    with pytest.raises(ProviderRequestError, match="500"):
        provider.generate("hola")


def test_http_error_with_unparseable_body_still_raises_provider_request_error():
    with patch("providers.anthropic.urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = _http_error(503, b"not json")
        provider = AnthropicProvider(_config())
        with pytest.raises(ProviderRequestError, match="503"):
            provider.generate("hola")


@patch("providers.anthropic.urllib.request.urlopen")
def test_connection_error_raises_provider_request_error(mock_urlopen):
    mock_urlopen.side_effect = urllib.error.URLError("no route to host")
    provider = AnthropicProvider(_config())

    with pytest.raises(ProviderRequestError):
        provider.generate("hola")


# 13. credencial nunca expuesta
@patch("providers.anthropic.urllib.request.urlopen")
def test_api_key_never_appears_in_exception_messages(mock_urlopen):
    mock_urlopen.side_effect = _http_error(401, {"error": {"message": "unauthorized"}})
    provider = AnthropicProvider(_config())

    with pytest.raises(ProviderRequestError) as exc_info:
        provider.generate("hola")

    assert FAKE_API_KEY not in str(exc_info.value)


def test_api_key_never_appears_in_provider_repr_or_str():
    provider = AnthropicProvider(_config())
    assert FAKE_API_KEY not in repr(provider)
    assert FAKE_API_KEY not in str(provider)


def test_api_key_never_appears_in_missing_credential_message():
    with pytest.raises(MissingCredentialError) as exc_info:
        AnthropicProvider(_config(api_key=None))
    assert FAKE_API_KEY not in str(exc_info.value)


# 14. registry resuelve "anthropic"
def test_registry_resolves_anthropic():
    provider = get_provider(_config())
    assert isinstance(provider, AnthropicProvider)


# 15. FakeProvider sigue funcionando (regresion trivial)
def test_fake_provider_still_works_after_adding_anthropic():
    from providers import FakeProvider

    provider = get_provider(ProviderConfig(provider="fake"))
    assert isinstance(provider, FakeProvider)
    assert provider.generate("x") == "fake response"


# Timeout configurable (ProviderConfig.timeout) cubierto por tests
@patch("providers.anthropic.urllib.request.urlopen")
def test_configured_timeout_is_passed_to_urlopen(mock_urlopen):
    mock_urlopen.return_value = _success_response()
    provider = AnthropicProvider(_config(timeout=12.5))

    provider.generate("hola")

    assert mock_urlopen.call_args.kwargs["timeout"] == 12.5


@patch("providers.anthropic.urllib.request.urlopen")
def test_default_timeout_used_when_not_configured(mock_urlopen):
    from providers.anthropic import DEFAULT_TIMEOUT_SECONDS

    mock_urlopen.return_value = _success_response()
    provider = AnthropicProvider(_config(timeout=None))

    provider.generate("hola")

    assert mock_urlopen.call_args.kwargs["timeout"] == DEFAULT_TIMEOUT_SECONDS


@patch("providers.anthropic.urllib.request.urlopen")
def test_non_positive_timeout_falls_back_to_default(mock_urlopen):
    from providers.anthropic import DEFAULT_TIMEOUT_SECONDS

    mock_urlopen.return_value = _success_response()
    provider = AnthropicProvider(_config(timeout=0))

    provider.generate("hola")

    assert mock_urlopen.call_args.kwargs["timeout"] == DEFAULT_TIMEOUT_SECONDS
