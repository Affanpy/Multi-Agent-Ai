from anthropic import AsyncAnthropic
from typing import AsyncGenerator, List, Dict
from providers.base import BaseProvider

class AnthropicProvider(BaseProvider):
    def _format_content(self, content) -> any:
        """Format konten pesan, termasuk multimodal (gambar)."""
        if isinstance(content, dict) and content.get("type") == "multimodal":
            return [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": content.get("content_type", "image/png"),
                        "data": content["image_base64"]
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
        client = AsyncAnthropic(api_key=api_key)
        
        filtered_messages = [m for m in messages if m["role"] in ["user", "assistant"]]
        
        anthropic_messages = []
        for msg in filtered_messages:
            role = "assistant" if msg["role"] != "user" else "user"
            content = self._format_content(msg.get("content", ""))
            
            # Jika konten multimodal (list), tidak bisa di-merge
            if isinstance(content, list):
                if len(anthropic_messages) > 0 and anthropic_messages[-1]["role"] == role:
                    # Tambahkan sebagai text ke pesan sebelumnya
                    anthropic_messages[-1]["content"] += f"\n\n{msg.get('content', {}).get('text', '')}" if isinstance(anthropic_messages[-1]["content"], str) else anthropic_messages[-1]["content"]
                else:
                    anthropic_messages.append({"role": role, "content": content})
            else:
                if len(anthropic_messages) > 0 and anthropic_messages[-1]["role"] == role and isinstance(anthropic_messages[-1]["content"], str):
                    anthropic_messages[-1]["content"] += f"\n\n{content}"
                else:
                    anthropic_messages.append({"role": role, "content": content})

        if len(anthropic_messages) > 0 and anthropic_messages[0]["role"] == "assistant":
             anthropic_messages.insert(0, {"role": "user", "content": "(Context started with assistant)"})

        async with client.messages.stream(
            max_tokens=max_tokens,
            messages=anthropic_messages,
            model=model,
            system=system_prompt,
            temperature=temperature
        ) as stream:
            async for text in stream.text_stream:
                if text:
                    yield text

    async def generate(
        self,
        api_key: str,
        model: str,
        system_prompt: str,
        messages: List[Dict],
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> str:
        client = AsyncAnthropic(api_key=api_key)
        
        filtered_messages = [m for m in messages if m["role"] in ["user", "assistant"]]
        
        anthropic_messages = []
        for msg in filtered_messages:
            role = "assistant" if msg["role"] != "user" else "user"
            content = self._format_content(msg.get("content", ""))
            
            if isinstance(content, list):
                anthropic_messages.append({"role": role, "content": content})
            else:
                if len(anthropic_messages) > 0 and anthropic_messages[-1]["role"] == role and isinstance(anthropic_messages[-1]["content"], str):
                    anthropic_messages[-1]["content"] += f"\n\n{content}"
                else:
                    anthropic_messages.append({"role": role, "content": content})

        if len(anthropic_messages) > 0 and anthropic_messages[0]["role"] == "assistant":
             anthropic_messages.insert(0, {"role": "user", "content": "(Context started with assistant)"})

        response = await client.messages.create(
            max_tokens=max_tokens,
            messages=anthropic_messages,
            model=model,
            system=system_prompt,
            temperature=temperature
        )
        
        return "".join([b.text for b in response.content if b.type == "text"])
