from abc import ABC, abstractmethod


class LLMPort(ABC):
    """Abstract port for LLM chat completion.

    Adapters must implement `chat()` and expose the active `model_name`.
    Swap providers (OpenAI, Ollama, vLLM, etc.) by injecting a different adapter
    — the application core never imports a concrete SDK.
    """

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Human-readable identifier of the model being used (e.g. 'gpt-4o-mini')."""
        ...

    @abstractmethod
    async def chat(self, messages: list[dict[str, str]]) -> str:
        """Run a chat completion and return the assistant reply as plain text.

        Args:
            messages: Ordered list of ``{"role": ..., "content": ...}`` dicts.
                      Roles: ``"system"``, ``"user"``, ``"assistant"``.
        Returns:
            The model's text reply.
        """
        ...
