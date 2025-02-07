from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, List

from openai import AsyncOpenAI
from zhipuai import ZhipuAI


class BaseGPTClient(ABC):
    def __init__(self, api_key: str, provider: str) -> None:
        self.api_key: str = api_key
        self.provider: str = provider

    def generate_prompt(self, releases: str, n_days: int, language: str = "English") -> str:
        """
        Generate the prompt using the GitHub releases JSON data.
        The prompt instructs to extract and summarize the important revision content,
        version number, and release time.
        """
        return (
            f"Please extract and summarize the important revision content, version number, "
            f"and release time from the following GitHub releases JSON data for the past {n_days} days. "
            f"Provide a concise summary in {language}.\n\n"
            f"Data:\n{releases}"
        )

    @abstractmethod
    async def stream_summary(
        self, releases: str, n_days: int, language: str = "English"
    ) -> AsyncGenerator[str, None]:
        """
        Stream the summary response from the GPT API.
        """
        pass


class OpenAIClient(BaseGPTClient):
    def __init__(self, api_key: str) -> None:
        super().__init__(api_key, provider="openai")
        self.client: AsyncOpenAI = AsyncOpenAI(api_key=api_key)

    async def stream_summary(
        self, releases: str, n_days: int, language: str = "English"
    ) -> AsyncGenerator[str, None]:
        prompt: str = self.generate_prompt(releases, n_days, language)
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": "You are a seasoned software engineer."},
            {"role": "user", "content": prompt},
        ]
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o",  # Use your preferred OpenAI model
                messages=messages,
                stream=True,
                temperature=0.0,
            )
            async for chunk in response:
                yield chunk.choices[0].delta.content or ""
        except Exception as e:
            yield f"\nError calling OpenAI API: {e}"


class ZhipuAIClient(BaseGPTClient):
    def __init__(self, api_key: str, model: str = "glm-4-plus") -> None:
        super().__init__(api_key, provider="zhipuai")
        self.client = ZhipuAI(api_key=api_key)
        self.model: str = model

    async def stream_summary(
        self, releases: str, n_days: int, language: str = "English"
    ) -> AsyncGenerator[str, None]:
        prompt: str = self.generate_prompt(releases, n_days, language)
        messages: List[Dict[str, Any]] = [
            {
                "role": "system",
                "content": "You are a knowledgeable assistant that provides professional and insightful advice.",
            },
            {"role": "user", "content": prompt},
        ]
        try:
            # ZhipuAI's API is synchronous; we iterate over its stream in an async function.
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True,
            )
            for chunk in response:
                yield chunk.choices[0].delta.content or ""
        except Exception as e:
            yield f"\nError calling ZhipuAI API: {e}"


def create_gpt_client(provider: str, api_key: str, model: str = "") -> BaseGPTClient:
    """
    Create a GPT client instance based on the provider.
    
    Supported providers: "openai" and "zhipuai".
    """
    provider = provider.lower()
    if provider == "openai":
        return OpenAIClient(api_key=api_key)
    elif provider == "zhipuai":
        model_to_use = model if model else "glm-4-flash"
        return ZhipuAIClient(api_key=api_key, model=model_to_use)
    else:
        raise ValueError(f"Unsupported GPT provider: {provider}")
