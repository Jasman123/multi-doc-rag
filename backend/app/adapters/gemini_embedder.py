from google import genai

from app.ports.embedder_port import EmbedderPort

_BATCH_SIZE = 100


class GeminiEmbedderAdapter(EmbedderPort):
    """EmbedderPort implementation backed by the Google Gemini Embeddings API."""

    def __init__(self, api_key: str, model: str) -> None:
        self._model = model
        self._client = genai.Client(api_key=api_key)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        all_embeddings: list[list[float]] = []

        for i in range(0, len(texts), _BATCH_SIZE):
            batch = texts[i : i + _BATCH_SIZE]
            response = await self._client.aio.models.embed_content(
                model=self._model, contents=batch
            )
            all_embeddings.extend(e.values for e in response.embeddings)

        return all_embeddings