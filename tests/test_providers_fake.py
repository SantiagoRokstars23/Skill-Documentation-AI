"""Tests de FakeProvider (V0.6)."""

from __future__ import annotations

from providers import FakeProvider, LLMProvider


def test_fake_provider_implements_llm_provider():
    provider = FakeProvider()
    assert isinstance(provider, LLMProvider)


def test_fake_provider_default_response():
    provider = FakeProvider()
    assert provider.generate("anything") == "fake response"


def test_fake_provider_configurable_response():
    provider = FakeProvider(response="custom canned response")
    assert provider.generate("anything") == "custom canned response"


def test_fake_provider_is_deterministic_across_calls():
    provider = FakeProvider(response="stable")
    results = {provider.generate(f"prompt {i}") for i in range(20)}
    assert results == {"stable"}


def test_fake_provider_ignores_prompt_content():
    provider = FakeProvider(response="same")
    assert provider.generate("a") == provider.generate("a completely different prompt")
