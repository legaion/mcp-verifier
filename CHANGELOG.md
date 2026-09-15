# Changelog — LEGAION Verifier MCP server

## 1.0.0 — 2026-09

- Five read-only tools: `verifier_engine`, `deep_xray`, `list_cases`, `list_clients`, `whoami`.
- OAuth 2.1 with PKCE and dynamic client registration; all metadata served from `mcp.legaion.com`.
- Registers queried live: ISAP, SAOS, EUR-Lex, UOKiK register of abusive clauses; national registers for other EU jurisdictions where a queryable source exists.
- Every verdict carries the register URL and the fetch timestamp.
- Deterministic scoring (`deterministic-v1`) and a publication gate (block / manual review / approved).
