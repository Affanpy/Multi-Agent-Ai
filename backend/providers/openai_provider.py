from openai import AsyncOpenAI
from typing import AsyncGenerator, List, Dict
from providers.base import BaseProvider

class OpenAIProvider(BaseProvider):
    def _format_content(self, content) -> any:
        """Format konten pesan, termasuk multimodal (gambar)."""
        if isinstance(content, dict) and content.get("type") == "multimodal":
            return [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{content.get('content_type', 'image/png')};base64,{content['image_base64']}"
                    }
                },
                {
                    "type": "text",
                    "text": content["text"]
                }
            ]
        return content if isinstance(content, str) else str(content)

    async def generate_stream(
        self,
        api_key: str,
        model: str,
        system_prompt: str,
        messages: List[Dict],
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> AsyncGenerator[str, None]:
        client = AsyncOpenAI(api_key=api_key)
        
        formatted_messages = [{"role": "system", "content": system_prompt}]
        for msg in messages:
            content = self._format_content(msg.get("content", ""))
            formatted_messages.append({"role": msg.get("role", "user"), "content": content})
        
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
        messages: List[Dict],
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> str:
        client = AsyncOpenAI(api_key=api_key)
        
        formatted_messages = [{"role": "system", "content": system_prompt}]
        for msg in messages:
            content = self._format_content(msg.get("content", ""))
            formatted_messages.append({"role": msg.get("role", "user"), "content": content})
        
        response = await client.chat.completions.create(
            model=model,
            messages=formatted_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False
        )
        
        return response.choices[0].message.content or ""
