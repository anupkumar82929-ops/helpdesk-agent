import os

# Any OpenAI-compatible provider works (Gemini free tier, Ollama, Groq, OpenAI...).
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash")
EMBED_MODEL = os.getenv("EMBED_MODEL", "gemini-embedding-001")
EMBED_DIM = int(os.getenv("EMBED_DIM", "768"))  # must match vector(N) in db/init.sql
EMBED_SEND_DIMENSIONS = os.getenv("EMBED_SEND_DIMENSIONS", "true").lower() == "true"

DATABASE_URL = os.getenv("DATABASE_URL", "")
MCP_DATABASE_URL = os.getenv("MCP_DATABASE_URL", "")
RAG_MIN_SIMILARITY = float(os.getenv("RAG_MIN_SIMILARITY", "0.30"))
DOCS_DIR = os.getenv("DOCS_DIR", "docs")
