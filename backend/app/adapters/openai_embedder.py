from openai import AsyncOpenAI

from app.ports.embedder_port import EmbedderPort

_BATCH_SIZE = 100


class OpenAIEmbedderAdapter(EmbedderPort):
    """EmbedderPort implementation backed by the OpenAI Embeddings API."""

    def __init__(self, api_key: str, model: str) -> None:
        self._model = model
        self._client = AsyncOpenAI(api_key=api_key)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        all_embeddings: list[list[float]] = []
        for i in range(0, len(texts), _BATCH_SIZE):
            batch = texts[i : i + _BATCH_SIZE]
            response = await self._client.embeddings.create(
                model=self._model, input=batch
            )
            all_embeddings.extend(item.embedding for item in response.data)
        return all_embeddings
