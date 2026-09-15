# Connecting to LEGAION Verifier

You need a LEGAION account (https://www.legaion.com — a free trial is available). The server uses OAuth 2.1 with dynamic client registration, so no API key is involved: the client opens a browser window, you sign in, the client receives a token scoped to your account.

Server URL for every client: **`https://mcp.legaion.com`**

## Claude (web and desktop)

1. Settings → Connectors → Add custom connector.
2. Name: `LEGAION Verifier`. URL: `https://mcp.legaion.com`. Leave client id and secret empty.
3. Click Add, then Connect. Sign in to LEGAION in the window that opens and approve access.
4. In a new chat, ask: *"Call whoami on LEGAION Verifier."* You should see your e-mail.

## Claude Code

```bash
claude mcp add --transport http legaion-verifier https://mcp.legaion.com
```

Then run `/mcp` inside Claude Code and authenticate when prompted.

## ChatGPT

Settings → Connectors → Create (Developer mode must be enabled by your workspace admin). Name `LEGAION Verifier`, MCP server URL `https://mcp.legaion.com`, authentication OAuth. Complete the sign-in.

## Cursor

Add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "legaion-verifier": {
      "url": "https://mcp.legaion.com"
    }
  }
}
```

Cursor will prompt for OAuth sign-in the first time a tool is called.

## Any other client

Use the Streamable HTTP transport with URL `https://mcp.legaion.com`. The server answers `401` with a `WWW-Authenticate` header pointing at `https://mcp.legaion.com/.well-known/oauth-protected-resource`; the authorization server metadata is at `https://mcp.legaion.com/.well-known/oauth-authorization-server`. Dynamic client registration is supported, PKCE (`S256`) is required.

`/sse` and `/mcp` are accepted as aliases of the root path for clients that expect them.

## First calls

```
whoami
→ { "id": "…", "email": "you@firm.pl", "clientId": "…" }

verifier_engine
  documentContent: "Zgodnie z art. 471 k.c. dłużnik obowiązany jest do naprawienia szkody… (por. wyrok SN z 12.03.2021, II CSK 331/12)"
  outputLanguage: "en"
→ claims[], overall verdict, sources with fetched_at
```

## Troubleshooting

- **Sign-in window closes but the client says "unauthorized"** — remove the connector and add it again; some clients cache a failed registration.
- **`list_cases` returns an empty list** — the account has no cases yet, or the plan does not include case management. `verifier_engine` still works.
- **A citation you know is real comes back `unverified`** — check the `sources` array: it tells you which register was asked and what it returned. Registers are occasionally down; the server does not fall back to guessing. Retry later or open an issue with the citation (never with client data).
