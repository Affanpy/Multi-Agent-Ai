from providers.openai_provider import OpenAIProvider
from providers.anthropic_provider import AnthropicProvider
from providers.gemini_provider import GeminiProvider

PROVIDERS = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "gemini": GeminiProvider
}

def get_provider(provider_name: str):
    if provider_name not in PROVIDERS:
        raise ValueError(f"Provider {provider_name} not supported")
    return PROVIDERS[provider_name]()
