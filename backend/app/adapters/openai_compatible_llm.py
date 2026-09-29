from openai import AsyncOpenAI

from app.ports.llm_port import LLMPort

class OpenAICompatibleLLMAdapter(LLMPort):
    def __init__(self, api_key: str | None, model: str, base_url: str | None = None, temperature: float = 0) -> None:
        self._model = model
        self._temperature = temperature
        self._client = AsyncOpenAI(api_key=api_key or "not-needed", base_url=base_url)

    @property
    def model_name(self) -> str:
        return self._model

    async def chat(self, messages: list[dict[str, str]]) -> str:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=self._temperature,
        )
        return response.choices[0].message.content or ""

    async def aclose(self) -> None:
        await self._client.close()