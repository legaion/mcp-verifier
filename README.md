# LEGAION Verifier — MCP server documentation

Remote MCP server that checks legal citations against the official registers they should come from, and records which register was queried, at what address, and at what time.

- Server URL: `https://mcp.legaion.com` (Streamable HTTP, OAuth 2.1 with dynamic client registration)
- Registry entry: `com.legaion/verifier` in the [Official MCP Registry](https://registry.modelcontextprotocol.io/v0.1/servers?search=com.legaion)
- Product site: https://www.legaion.com
- Publisher: Aidvocates, Inc. (DBA LEGAION), New York · EU engineering: Katowice, Poland

This repository contains **documentation only**: the tool schemas the server exposes, how to connect from MCP clients, what the outputs mean, and what the server does not do. The server code is not open source. The [`sygnatury/`](sygnatury/) directory contains a small, independent, MIT-licensed validator for Polish court case signature formats.

Polska wersja: [README.pl.md](README.pl.md)

---

## What the server does

Lawyers cite statutes and court decisions. Language models produce citations that look right and are sometimes invented. LEGAION Verifier takes a document, extracts every legal claim (statute article, case signature, legal thesis), and checks each one against the official source it should come from — ISAP (Polish statutes), SAOS (Polish court decisions), EUR-Lex (EU law), plus national registers for other EU jurisdictions where coverage exists. Every verdict carries the register URL and the timestamp of the actual fetch, so a reviewer can repeat the check.

The design rule is simple: **no citation is marked verified unless the register answered**. A register that is down, or a citation the register does not know, produces `unverified` or `unknown`, never a green light.

## Tools

All five tools are read-only (`readOnlyHint: true`, `destructiveHint: false`). The server never writes to the user's documents, never sends e-mail, never changes anything outside the optional "attach verification result to a case" step described below.

| Tool | Purpose | Required input |
|---|---|---|
| `verifier_engine` | Verify legal citations and claims in a document. Returns claims with verdicts (`verified` / `unverified` / `fabricated` / `unknown`), sources (register URL + `fetched_at`), an overall verdict and reasoning. | `documentContent` |
| `deep_xray` | Risk audit of a contract, terms of service or consumer template. Returns risks by level (critical/high/medium/low), clause statuses, recommendations and a numeric score. Mode `klauzule_abuzywne` adds matches against the Polish UOKiK register of abusive clauses, with entry number, URL and fetch timestamp. | `documentContent` |
| `list_cases` | List the signed-in user's LEGAION cases, optionally filtered by status. | — |
| `list_clients` | List the signed-in user's LEGAION clients (company, contact, e-mail). | — |
| `whoami` | Return the signed-in user's id, e-mail and OAuth client id. Use to confirm the connection works. | — |

Full JSON Schemas: [`tools/tools.json`](tools/tools.json). Output format of `verifier_engine`: [`docs/verifier-output.md`](docs/verifier-output.md).

`list_cases`, `list_clients` and the optional `caseId` parameter of `verifier_engine` require a LEGAION account with the platform plan. `verifier_engine` and `deep_xray` work with any LEGAION account, including the Verifier-only plan.

## Connecting

See [`docs/connect.md`](docs/connect.md) for step-by-step instructions for Claude (web, desktop, Claude Code), ChatGPT, Cursor and any client that supports remote MCP servers with OAuth.

Short version: add `https://mcp.legaion.com` as a remote MCP server, complete the sign-in in the browser window that opens, then call `whoami`.

## Data handling

- The server runs under the signed-in user's row-level permissions. One organisation cannot see another's cases, clients or verification results.
- Document content sent to `verifier_engine` or `deep_xray` is processed for the request and is **not stored**. If you pass `caseId`, only the verification result (claims, verdicts, sources) is attached to the case — the document text is not.
- Registers are queried live. The `fetched_at` timestamp in every source is the time of that query.
- Details: https://www.legaion.com/privacy

## What it does not do

- It does not judge whether a citation is *relevant* to your argument — only whether it exists in the register in the form cited and whether the quoted content matches.
- Coverage outside Poland and EU law depends on whether the national register offers a queryable source. Where it does not, the verdict is `unknown` with an explanation, not a guess.
- It does not draft, summarise or rewrite documents.
- It is a tool for the professional who signs the document. It does not replace that professional's review.

## Support

- Issues about this documentation: open an issue in this repository.
- Server problems, account questions: office@aidvocates.com
- Status and changes: [`CHANGELOG.md`](CHANGELOG.md)

## Licence

Documentation in this repository: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Code in [`sygnatury/`](sygnatury/): MIT. The LEGAION Verifier server itself is proprietary and is not covered by either licence.
