from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.ports.llm_port import LLMPort


class OpenAILLMAdapter(LLMPort):
    """LLMPort implementation backed by OpenAI chat models via LangChain."""

    def __init__(self, api_key: str, model: str, temperature: float = 0) -> None:
        self._model = model
        self._llm = ChatOpenAI(model=model, temperature=temperature, api_key=api_key)

    @property
    def model_name(self) -> str:
        return self._model

    async def chat(self, messages: list[dict[str, str]]) -> str:
        role_map = {
            "system": SystemMessage,
            "user": HumanMessage,
            "assistant": AIMessage,
        }
        lc_messages = [
            role_map[m["role"]](content=m["content"]) for m in messages
        ]
        result = await self._llm.ainvoke(lc_messages)
        return str(result.content)
