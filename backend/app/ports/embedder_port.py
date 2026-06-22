from abc import ABC, abstractmethod


class EmbedderPort(ABC):
    """Abstract port for text embedding.

    Adapters must implement `embed()`.
    Swap embedding providers (OpenAI, sentence-transformers, local GGUF, etc.)
    by injecting a different adapter — the application core never imports a
    concrete SDK.
    """

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts and return their dense vectors.

        Args:
            texts: Strings to embed (can be 1 or many).
        Returns:
            A list of float vectors, one per input string, in the same order.
        """
        ...
