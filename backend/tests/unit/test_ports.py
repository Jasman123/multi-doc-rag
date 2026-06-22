"""Verify that LLMPort and EmbedderPort enforce their ABC contracts."""
import pytest

from app.ports.embedder_port import EmbedderPort
from app.ports.llm_port import LLMPort


# ── LLMPort ──────────────────────────────────────────────────────────────────

def test_llm_port_cannot_be_instantiated_directly():
    with pytest.raises(TypeError):
        LLMPort()  # type: ignore[abstract]


def test_llm_port_missing_chat_raises():
    class MissingChat(LLMPort):
        @property
        def model_name(self) -> str:
            return "x"
        # chat() not implemented

    with pytest.raises(TypeError):
        MissingChat()


def test_llm_port_missing_model_name_raises():
    class MissingName(LLMPort):
        async def chat(self, messages):
            return ""
        # model_name not implemented

    with pytest.raises(TypeError):
        MissingName()


def test_llm_port_full_implementation_ok():
    class FullLLM(LLMPort):
        @property
        def model_name(self) -> str:
            return "my-llm"

        async def chat(self, messages):
            return "hello"

    obj = FullLLM()
    assert obj.model_name == "my-llm"


# ── EmbedderPort ─────────────────────────────────────────────────────────────

def test_embedder_port_cannot_be_instantiated_directly():
    with pytest.raises(TypeError):
        EmbedderPort()  # type: ignore[abstract]


def test_embedder_port_missing_embed_raises():
    class MissingEmbed(EmbedderPort):
        pass  # embed() not implemented

    with pytest.raises(TypeError):
        MissingEmbed()


def test_embedder_port_full_implementation_ok():
    class FullEmbedder(EmbedderPort):
        async def embed(self, texts):
            return [[0.0] for _ in texts]

    obj = FullEmbedder()
    assert obj is not None


@pytest.mark.asyncio
async def test_fake_llm_records_calls(fake_llm):
    messages = [{"role": "user", "content": "Hello"}]
    result = await fake_llm.chat(messages)
    assert result == "Test answer from fake LLM."
    assert fake_llm.calls == [messages]


@pytest.mark.asyncio
async def test_fake_embedder_returns_correct_shape(fake_embedder):
    texts = ["hello", "world", "foo"]
    embeddings = await fake_embedder.embed(texts)
    assert len(embeddings) == 3
    assert all(len(v) == 4 for v in embeddings)
