import os
import base64
from typing import AsyncGenerator, List, Dict
from google import genai
from google.genai import types
from providers.base import BaseProvider

class GeminiProvider(BaseProvider):
    def _format_messages(self, messages: List[Dict]) -> List[types.Content]:
        formatted = []
        for msg in messages:
            role = "model" if msg["role"] != "user" else "user"
            content = msg.get("content", "")
            
            # Handle multimodal content (gambar)
            if isinstance(content, dict) and content.get("type") == "multimodal":
                parts = [types.Part.from_text(text=content["text"])]
                # Tambahkan gambar sebagai inline data
                image_bytes = base64.b64decode(content["image_base64"])
                parts.append(types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=content.get("content_type", "image/png")
                ))
                
                if len(formatted) > 0 and formatted[-1].role == role:
                    formatted[-1].parts.extend(parts)
                else:
                    formatted.append(types.Content(role=role, parts=parts))
            else:
                text = content if isinstance(content, str) else str(content)
                if len(formatted) > 0 and formatted[-1].role == role:
                    formatted[-1].parts[0].text += f"\n\n{text}"
                else:
                    formatted.append(types.Content(role=role, parts=[types.Part.from_text(text=text)]))
                
        if len(formatted) > 0 and formatted[0].role == "model":
             formatted.insert(0, types.Content(role="user", parts=[types.Part.from_text(text="(Context started with model)")]))

        return formatted

    async def generate_stream(
        self,
        api_key: str,
        model: str,
        system_prompt: str,
        messages: List[Dict],
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> AsyncGenerator[str, None]:
        client = genai.Client(api_key=api_key)
        
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        
        formatted_messages = self._format_messages(messages)
        
        response = client.models.generate_content_stream(
            model=model,
            contents=formatted_messages,
            config=config
        )
        
        for chunk in response:
            if chunk.text:
                yield chunk.text

    async def generate(
        self,
        api_key: str,
        model: str,
        system_prompt: str,
        messages: List[Dict],
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> str:
        client = genai.Client(api_key=api_key)
        
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        
        formatted_messages = self._format_messages(messages)
        
        response = client.models.generate_content(
            model=model,
            contents=formatted_messages,
            config=config
        )
        
        return response.text
