import pytest

from providers import LLMProvider


def test_llm_provider_cannot_be_instantiated_directly():
    with pytest.raises(TypeError):
        LLMProvider()


def test_llm_provider_subclass_must_implement_generate():
    class EchoProvider(LLMProvider):
        def generate(self, prompt: str) -> str:
            return prompt

    provider = EchoProvider()

    assert provider.generate("hello") == "hello"
