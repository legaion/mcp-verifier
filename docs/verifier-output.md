# `verifier_engine` — output format

The response has two top-level objects: `verifier` (the full record) and `summary` (a compact view for clients that only need verdicts). Example below is a real response for a three-sentence test document (one correct statute, one court decision cited with a wrong date, one non-existent article), trimmed for length.

```json
{
  "verifier": {
    "verificationStatus": "partial",
    "overallScore": 33,
    "overallVerdict": "partially_verified",
    "summary": "Twierdzenie 1 odpowiada treści jednostki redakcyjnej z rejestru … Twierdzenie 3 nie mogło zostać sprawdzone, ponieważ treści jednostki redakcyjnej nie udało się pobrać.",
    "claims": [
      {
        "id": 1,
        "assertionType": "DC",
        "legalBasis": "art. 471 Kodeksu cywilnego",
        "spanOffset": { "start": 0, "end": 148, "paragraph": 1 },
        "verdict": "verified",
        "confidence": 99,
        "sourceConfirmed": true,
        "physicallyFetched": true,
        "unitCheck": {
          "registry": "ISAP",
          "status": "found",
          "unitLabel": "art. 471",
          "registryText": "Art. 471. Dłużnik obowiązany jest do naprawienia szkody …",
          "sourceUrl": "https://isap.sejm.gov.pl/isap.nsf/DocDetails.xsp?id=WDU19640160093#art471",
          "fetchedAt": "2026-09-15T15:55:03.950Z"
        },
        "hash": "c57377fc…"
      },
      {
        "id": 3,
        "assertionType": "HF",
        "legalBasis": "art. 9999 k.c.",
        "verdict": "unverified",
        "confidence": 10,
        "sourceConfirmed": false,
        "physicallyFetched": false,
        "unitCheck": {
          "status": "unavailable",
          "registry": null,
          "sourceUrl": null,
          "fetchedAt": "2026-09-15T15:55:34.389Z",
          "note": "Kontrola powołania nie doszła do skutku (HTTP 546) — powołania nie sprawdzono"
        }
      }
    ],
    "citations": [
      {
        "id": 1,
        "source": "ISAP",
        "url": "https://isap.sejm.gov.pl/isap.nsf/DocDetails.xsp?id=WDU19640160093#art471",
        "quote": "Dłużnik obowiązany jest do naprawienia szkody …",
        "fetchedAt": "2026-09-15T15:55:03.950Z",
        "physicallyFetched": true,
        "registryStatus": "potwierdzone pobraniem z rejestru",
        "claimId": 1
      }
    ],
    "verdictCounts": { "total": 3, "verified": 1, "unverified": 2, "fabricated": 0, "unknown": 0 },
    "scoreBreakdown": {
      "score": 33,
      "method": "deterministic-v1",
      "claimsTotal": 3,
      "sourceRequiredTotal": 3,
      "physicallyVerified": 1,
      "reasons": [
        "Twierdzenia: 3, w tym powołujące źródło: 3 (zweryfikowane 1, ostrzeżenia 2, błędy 0).",
        "Fizycznie potwierdzone źródła: 1/3."
      ]
    },
    "publicationGate": {
      "decision": "BLOCKED",
      "threshold": 50,
      "manualReviewThreshold": 70,
      "score": 33,
      "blockReasons": ["Wynik weryfikacji (33%) poniżej progu blokady (50%)"]
    },
    "dualModelVerification": {
      "enabled": true,
      "sameModel": false,
      "extractedClaimsCount": 3,
      "generatorStartedAt": "2026-09-15T15:54:52.540Z",
      "auditorCompletedAt": "2026-09-15T15:55:50.256Z"
    },
    "auditTrace": {
      "requestHash": "b19eeb9a…",
      "generatorOutputHash": "b52a57a3…",
      "auditorOutputHash": "2bd480c9…"
    }
  },
  "summary": {
    "overallVerdict": "partially_verified",
    "score": 33,
    "claimsCount": 3,
    "claims": [
      { "verdict": "verified",   "confidence": 99, "sourceUrl": "https://isap.sejm.gov.pl/…#art471", "fetchedAt": "2026-09-15T15:55:03.950Z" },
      { "verdict": "unverified", "confidence": 35, "sourceUrl": null, "fetchedAt": null },
      { "verdict": "unverified", "confidence": 10, "sourceUrl": null, "fetchedAt": null }
    ]
  }
}
```

## Fields that matter

| Field | Meaning |
|---|---|
| `claims[].verdict` | `verified` — the register returned the unit and its text matches the claim. `unverified` — the register could not confirm it (unit not found, register unavailable, or text does not support the claim). `fabricated` — the register confirmed the unit does not exist. `unknown` — no queryable register for this jurisdiction. |
| `claims[].assertionType` | `DC` — direct citation of a statute unit. `HF` — hard fact (court decision, date, number, quoted thesis). Other types may appear for derived statements. |
| `claims[].spanOffset` | Character range of the claim in `documentContent`, so a client can highlight it. |
| `claims[].unitCheck` | The register query itself: which register, what it answered, the URL and `fetchedAt`. `status: "unavailable"` with a `note` means the query did not complete — the claim is **not** marked verified in that case. |
| `claims[].physicallyFetched` | `true` only when the server actually retrieved the unit from the register during this request. |
| `citations[]` | Sources found, with quote, URL and `fetchedAt`, linked to claims by `claimId`. |
| `scoreBreakdown` | How `overallScore` was computed. The score is deterministic from the verdicts (`method: deterministic-v1`); a model's own estimate is discarded if it disagrees. |
| `publicationGate` | `APPROVED` (score ≥ manual-review threshold), `MANUAL_REVIEW`, or `BLOCKED` (below `threshold`). This is advice for the professional, not an action the server takes. |
| `dualModelVerification` | Two independent stages: extraction and audit. Engines are not named in the output. |
| `auditTrace` | SHA-256 hashes of the request and both stage outputs, so a stored result can be tied to the exact input later. |

## Reading a result

1. Look at `verdictCounts` and `publicationGate.decision` first.
2. For every claim that is not `verified`, read `unitCheck.note` and `unitCheck.status`: it tells you whether the register said *no* or did not answer. Those are different situations and the server keeps them apart.
3. `fetchedAt` is the time of the live register query. If you need to reproduce the check, open `sourceUrl`.

## Known limitations of this version

- A citation the register cannot resolve is reported as `unverified`, not `fabricated`, unless the register explicitly confirmed absence. Expect `fabricated` to be rare.
- A court decision cited with a wrong date but a correct signature comes back `unverified`; the discrepancy is visible in `citations[].quote`, not as a dedicated flag.
- `summary.claims[].text` is currently `null`; use `verifier.claims[].legalBasis` and `spanOffset` instead.
