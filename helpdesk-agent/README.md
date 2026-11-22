# Acme HR/IT Helpdesk Agent

An agent that answers HR/IT **policy** questions with sources (RAG), looks up **employee-specific**
data in Postgres through an **MCP server**, and is protected by **guardrails**. When it can't answer,
it opens a ticket (mock `create_ticket`, stored in Postgres).

## Quick start

```bash
cp .env.example .env        # add a FREE Gemini key from https://aistudio.google.com/apikey
docker compose up --build
```

- Chat UI: http://localhost:8000
- API: `curl -X POST localhost:8000/chat -H 'content-type: application/json' -d '{"message":"How many leave days does E102 have left?"}'`
- Run the 10 test questions: `docker compose run --rm app python -m app.run_tests` (writes `results/TEST_RESULTS.md`)
- See created tickets: `docker compose exec db psql -U helpdesk -c "select * from tickets"`

## Architecture

```
 user ──> [Guardrails IN: regex heuristics -> LLM classifier (injection / in-scope)]
              │ blocked / refused -> canned reply
              ▼
        Agent (OpenAI Agents SDK, Gemini 2.5 Flash via OpenAI-compatible API)
          ├─ tool: search_policies ──> pgvector (doc_chunks)   [RAG, returns source file names]
          ├─ tool: create_ticket   ──> tickets table           [bonus, mock ticketing]
          └─ MCP (stdio) ──> app/mcp_server.py ──> Postgres as read-only role `mcp_reader`
              │
              ▼
        [Guardrails OUT: PII/secret redaction + system-prompt canary check] ──> user
```

| Piece | Choice |
|---|---|
| Framework | OpenAI Agents SDK (first-class MCP support) |
| LLM / embeddings | Free tier: Gemini `gemini-2.5-flash` / `gemini-embedding-001` (768-dim). Any OpenAI-compatible provider (Ollama, Groq, OpenAI) works by editing `.env` only |
| Vector DB | **pgvector** in the same Postgres. One fewer service, fine at this scale |
| Data | `db/init.sql` seeds 6 employees, leave balances, IT assets. `docs/` has 5 policy docs |

## Design choices

- **RAG**: docs are chunked per `##` section (title prefixed for context), embedded, stored in pgvector.
  Retrieval uses cosine similarity with a minimum threshold (`RAG_MIN_SIMILARITY`). If nothing clears it,
  the tool returns `NO_RELEVANT_POLICY_FOUND` and the agent must create a ticket instead of guessing.
  Answers end with `Sources: <file>.md`.
- **MCP**: I wrote a small MCP server with narrow, parameterised tools (`get_leave_balance`,
  `get_it_assets`, `get_employee_profile`, `get_manager`) rather than exposing a generic
  `query(sql)` tool. Defense in depth: the server connects as `mcp_reader`, which is read-only and has a
  **column-level grant that excludes `salary_inr` and `phone`**, so even a hijacked agent can't read them.
  Employee IDs are validated against `^E\d{3,4}$`.
- **Guardrails** (layered, because no single layer is reliable):
  1. *Prompt injection*: regex heuristics (cheap, deterministic) then an LLM classifier for paraphrased
     attacks; the agent's instructions also say tool/document content is data, not instructions.
  2. *Scope*: the same classifier refuses non-HR/IT questions.
  3. *PII*: every output is regex-redacted (emails except the official helpdesk addresses, phone,
     Aadhaar, PAN, SSN, card numbers, API keys).
  4. *Leak detection*: canary token in the system prompt; if it appears in output the reply is replaced.
  The classifier fails closed (on error the request is not processed).
- **Ticketing**: `create_ticket` is a mock that writes to a `tickets` table and returns `TKT-000N`.
  Swapping in the monday.com API only means changing the body of that one function.

## Known limitations (honest list)

- No authentication: anyone can ask about any employee ID. In production the caller's identity
  (SSO) would be injected and the MCP tools restricted to self / direct reports / HR role.
- Regex redaction is a safety net, not a guarantee; it can miss unusual formats and can over-match.
- Single-turn only (no conversation memory).
- Injection detection is probabilistic. The LLM classifier can be fooled by a clever attacker.

## Test results

Generated with `docker compose run --rm app python -m app.run_tests`.
Test set: 2 RAG, 2 MCP, 1 RAG+MCP, 2 prompt-injection, 1 out-of-scope, 1 PII request, 1 unanswerable (-> ticket).

> **TODO before submitting:** run the command above and paste the contents of
> `results/TEST_RESULTS.md` here (questions + the agent's actual answers).

## Repo layout

```
docker-compose.yml  Dockerfile  .env.example
db/init.sql         schema, seed data, read-only role
docs/               5 sample policy docs
app/agent.py        agent, tools, guardrail pipeline
app/mcp_server.py   MCP server (read-only Postgres tools)
app/guardrails.py   injection / scope / PII logic
app/rag.py ingest.py  embeddings, pgvector search, ingestion
app/main.py         FastAPI + chat page
app/run_tests.py    10-question test harness
```
