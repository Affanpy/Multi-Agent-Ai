from anthropic import AsyncAnthropic
from typing import AsyncGenerator, List, Dict
from providers.base import BaseProvider

class AnthropicProvider(BaseProvider):
    async def generate_stream(
        self,
        api_key: str,
        model: str,
        system_prompt: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> AsyncGenerator[str, None]:
        client = AsyncAnthropic(api_key=api_key)
        
        # Anthropic doesn't allow 'system' role in messages list, it's passed as a separate param
        filtered_messages = [m for m in messages if m["role"] in ["user", "assistant"]]
        
        # In Anthropic, assistant messages require alternating roles user/assistant. 
        # Our base messages might have two assistants back to back if two agents replied.
        # We need to coalesce/format them logically, but Anthropic API requires strict alternating roles.
        # Let's map any non-user to 'assistant'. Sometimes we might need to merge contiguous roles.
        anthropic_messages = []
        for msg in filtered_messages:
            role = "assistant" if msg["role"] != "user" else "user"
            
            if len(anthropic_messages) > 0 and anthropic_messages[-1]["role"] == role:
                anthropic_messages[-1]["content"] += f"\n\n{msg['content']}"
            else:
                anthropic_messages.append({"role": role, "content": msg['content']})

        # Ensure first message is user
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
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> str:
        client = AsyncAnthropic(api_key=api_key)
        
        filtered_messages = [m for m in messages if m["role"] in ["user", "assistant"]]
        
        anthropic_messages = []
        for msg in filtered_messages:
            role = "assistant" if msg["role"] != "user" else "user"
            if len(anthropic_messages) > 0 and anthropic_messages[-1]["role"] == role:
                anthropic_messages[-1]["content"] += f"\n\n{msg['content']}"
            else:
                anthropic_messages.append({"role": role, "content": msg['content']})

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
