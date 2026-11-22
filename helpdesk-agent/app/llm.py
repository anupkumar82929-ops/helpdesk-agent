"""Central OpenAI-compatible clients (provider is chosen purely via .env)."""
from openai import AsyncOpenAI, OpenAI

from .config import LLM_API_KEY, LLM_BASE_URL

sync_client = OpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY or "none")
async_client = AsyncOpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY or "none")
