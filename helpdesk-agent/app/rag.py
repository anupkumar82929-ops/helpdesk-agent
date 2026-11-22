"""RAG layer: embeddings + pgvector similarity search."""
import psycopg2
from .config import DATABASE_URL, EMBED_DIM, EMBED_MODEL, EMBED_SEND_DIMENSIONS, RAG_MIN_SIMILARITY
from .llm import sync_client


def embed(texts: list[str]) -> list[list[float]]:
    out: list[list[float]] = []
    for i in range(0, len(texts), 50):  # small batches to respect free-tier limits
        kwargs = {"model": EMBED_MODEL, "input": texts[i:i + 50]}
        if EMBED_SEND_DIMENSIONS:
            kwargs["dimensions"] = EMBED_DIM
        resp = sync_client.embeddings.create(**kwargs)
        out.extend(d.embedding for d in resp.data)
    return out


def to_pgvector(vec: list[float]) -> str:
    return "[" + ",".join(f"{x:.6f}" for x in vec) + "]"


def search(query: str, k: int = 4) -> list[dict]:
    """Return top-k chunks above the similarity threshold."""
    qvec = to_pgvector(embed([query])[0])
    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT source, chunk_index, content,
                          1 - (embedding <=> %s::vector) AS similarity
                   FROM doc_chunks
                   ORDER BY embedding <=> %s::vector
                   LIMIT %s""",
                (qvec, qvec, k),
            )
            rows = cur.fetchall()
    finally:
        conn.close()
    return [
        {"source": r[0], "chunk": r[1], "content": r[2], "similarity": float(r[3])}
        for r in rows
        if float(r[3]) >= RAG_MIN_SIMILARITY
    ]
