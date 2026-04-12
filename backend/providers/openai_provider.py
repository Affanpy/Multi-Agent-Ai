from openai import AsyncOpenAI
from typing import AsyncGenerator, List, Dict
from providers.base import BaseProvider

class OpenAIProvider(BaseProvider):
    async def generate_stream(
        self,
        api_key: str,
        model: str,
        system_prompt: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> AsyncGenerator[str, None]:
        client = AsyncOpenAI(api_key=api_key)
        
        formatted_messages = [{"role": "system", "content": system_prompt}] + messages
        
        response = await client.chat.completions.create(
            model=model,
            messages=formatted_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )
        
        async for chunk in response:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta

    async def generate(
        self,
        api_key: str,
        model: str,
        system_prompt: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> str:
        client = AsyncOpenAI(api_key=api_key)
        formatted_messages = [{"role": "system", "content": system_prompt}] + messages
        
        response = await client.chat.completions.create(
            model=model,
            messages=formatted_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False
        )
        
        return response.choices[0].message.content or ""
