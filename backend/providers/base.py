from abc import ABC, abstractmethod
from typing import AsyncGenerator, List, Dict, Any

class BaseProvider(ABC):
    @abstractmethod
    async def generate_stream(
        self,
        api_key: str,
        model: str,
        system_prompt: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> AsyncGenerator[str, None]:
        """
        Yields tokens one by one as they are generated.
        Messages format: [{'role': 'user', 'content': 'hello'}, ...]
        """
        pass
        
    @abstractmethod
    async def generate(
        self,
        api_key: str,
        model: str,
        system_prompt: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> str:
        """
        Returns the complete response string.
        """
        pass
