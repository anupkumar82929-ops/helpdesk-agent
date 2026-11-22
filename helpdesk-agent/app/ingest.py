"""Chunk policy docs by section, embed them, and store in pgvector. Idempotent."""
import pathlib
import re

import psycopg2

from .config import DATABASE_URL, DOCS_DIR
from .rag import embed, to_pgvector


def chunk_markdown(text: str) -> list[str]:
    """One chunk per '## ' section, prefixed with the doc title for context."""
    title_match = re.match(r"#\s+(.+)", text)
    title = title_match.group(1) if title_match else ""
    sections = re.split(r"\n(?=## )", text)
    chunks = []
    for sec in sections:
        sec = sec.strip()
        if not sec.startswith("## "):
            continue  # the title block
        chunks.append(f"{title}\n{sec}")
    return chunks


def main():
    files = sorted(pathlib.Path(DOCS_DIR).glob("*.md"))
    records = []
    for f in files:
        for i, chunk in enumerate(chunk_markdown(f.read_text())):
            records.append((f.name, i, chunk))
    print(f"Ingesting {len(records)} chunks from {len(files)} docs...")
    vectors = embed([r[2] for r in records])

    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn, conn.cursor() as cur:
            cur.execute("TRUNCATE doc_chunks RESTART IDENTITY")
            for (src, idx, content), vec in zip(records, vectors):
                cur.execute(
                    "INSERT INTO doc_chunks (source, chunk_index, content, embedding) "
                    "VALUES (%s, %s, %s, %s::vector)",
                    (src, idx, content, to_pgvector(vec)),
                )
    finally:
        conn.close()
    print("Ingestion complete.")


if __name__ == "__main__":
    main()
