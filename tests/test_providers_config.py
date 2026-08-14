"""Tests de ProviderConfig (V0.6; campo `timeout` agregado en V0.7)."""

from __future__ import annotations

import dataclasses

import pytest

from providers import ProviderConfig


def test_construction_with_explicit_values():
    config = ProviderConfig(provider="fake", model="fake-model", api_key="secret")
    assert config.provider == "fake"
    assert config.model == "fake-model"
    assert config.api_key == "secret"


def test_defaults_are_none():
    config = ProviderConfig(provider="fake")
    assert config.model is None
    assert config.api_key is None
    assert config.timeout is None


def test_is_immutable():
    config = ProviderConfig(provider="fake")
    with pytest.raises(dataclasses.FrozenInstanceError):
        config.provider = "other"  # type: ignore[misc]


def test_api_key_never_appears_in_repr():
    config = ProviderConfig(provider="fake", api_key="super-secret-value")
    assert "super-secret-value" not in repr(config)


def test_api_key_never_appears_in_str():
    config = ProviderConfig(provider="fake", api_key="super-secret-value")
    assert "super-secret-value" not in str(config)


def test_from_env_reads_prefixed_variables(monkeypatch):
    monkeypatch.setenv("SPRING_DOC_LLM_PROVIDER", "fake")
    monkeypatch.setenv("SPRING_DOC_LLM_MODEL", "fake-model")
    monkeypatch.setenv("SPRING_DOC_LLM_API_KEY", "secret-from-env")
    monkeypatch.setenv("SPRING_DOC_LLM_TIMEOUT", "45")

    config = ProviderConfig.from_env()

    assert config.provider == "fake"
    assert config.model == "fake-model"
    assert config.api_key == "secret-from-env"
    assert config.timeout == 45.0


def test_from_env_missing_variables_yields_empty_provider_and_none_fields(monkeypatch):
    monkeypatch.delenv("SPRING_DOC_LLM_PROVIDER", raising=False)
    monkeypatch.delenv("SPRING_DOC_LLM_MODEL", raising=False)
    monkeypatch.delenv("SPRING_DOC_LLM_API_KEY", raising=False)
    monkeypatch.delenv("SPRING_DOC_LLM_TIMEOUT", raising=False)

    config = ProviderConfig.from_env()

    assert config.provider == ""
    assert config.model is None
    assert config.api_key is None
    assert config.timeout is None


def test_from_env_custom_prefix(monkeypatch):
    monkeypatch.setenv("OTHER_PREFIX_PROVIDER", "fake")
    config = ProviderConfig.from_env(prefix="OTHER_PREFIX_")
    assert config.provider == "fake"


def test_from_env_invalid_timeout_falls_back_to_none(monkeypatch):
    monkeypatch.setenv("SPRING_DOC_LLM_PROVIDER", "fake")
    monkeypatch.setenv("SPRING_DOC_LLM_TIMEOUT", "not-a-number")

    config = ProviderConfig.from_env()

    assert config.timeout is None


def test_timeout_can_be_set_explicitly():
    config = ProviderConfig(provider="anthropic", timeout=12.5)
    assert config.timeout == 12.5
