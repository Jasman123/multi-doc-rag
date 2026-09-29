from unittest.mock import AsyncMock, patch

import pytest

from app.adapters.openai_compatible_embedder import OpenAICompatibleEmbedderAdapter
from app.adapters.openai_compatible_llm import OpenAICompatibleLLMAdapter


def _fake_chat_response(content: str):
    message = type("M", (), {"content": content})()
    choice = type("C", (), {"message": message})()
    return type("R", (), {"choices": [choice]})()


@pytest.mark.asyncio
async def test_chat_passes_messages_through_unchanged():
    with patch("app.adapters.openai_compatible_llm.AsyncOpenAI") as mock_cls:
        mock_client = mock_cls.return_value
        mock_client.chat.completions.create = AsyncMock(return_value=_fake_chat_response("hi"))

        adapter = OpenAICompatibleLLMAdapter(api_key="k", model="gpt-4o-mini", temperature=0.2)
        messages = [{"role": "system", "content": "s"}, {"role": "user", "content": "u"}]
        result = await adapter.chat(messages)

        assert result == "hi"
        assert adapter.model_name == "gpt-4o-mini"
        mock_client.chat.completions.create.assert_awaited_once_with(
            model="gpt-4o-mini", messages=messages, temperature=0.2
        )


def test_missing_api_key_uses_placeholder_not_none():
    with patch("app.adapters.openai_compatible_llm.AsyncOpenAI") as mock_cls:
        OpenAICompatibleLLMAdapter(api_key=None, model="llama3.1", base_url="http://localhost:11434/v1")
        _, kwargs = mock_cls.call_args
        assert kwargs["api_key"]
        assert kwargs["base_url"] == "http://localhost:11434/v1"


@pytest.mark.asyncio
async def test_embed_batches_above_100_texts():
    with patch("app.adapters.openai_compatible_embedder.AsyncOpenAI") as mock_cls:
        mock_client = mock_cls.return_value

        async def fake_create(model, input):
            data = [type("D", (), {"embedding": [0.0]})() for _ in input]
            return type("R", (), {"data": data})()

        mock_client.embeddings.create = AsyncMock(side_effect=fake_create)

        adapter = OpenAICompatibleEmbedderAdapter(api_key="k", model="text-embedding-3-small")
        result = await adapter.embed(["t"] * 150)

        assert len(result) == 150
        assert mock_client.embeddings.create.await_count == 2  # batches of 100 + 50
