# Reed Intel Editorial Policy

## Core Principle
The system detects signals. Human editors decide what gets published.

## Editorial Queue Status Flow
```
new → needs_research → verified → needs_editor_review → approved_for_article → published
                                                       ↘ rejected
```

## AI Drafting Rules
- AI drafting is **disabled by default**
- Enable only for items with `status = 'verified'` and `confidence_score >= 0.75`
- AI must use only structured fields already in the database
- AI must NOT invent quotes, dollar values, relationships, or people
- All AI drafts carry status `draft` until a human editor approves
- Mark uncertainty as "requires editor verification"

## Confidence Score Guide
| Score | Meaning | Action |
|-------|---------|--------|
| 0.90+ | High confidence | Auto-route to editorial queue |
| 0.75–0.89 | Good signal | Queue for review |
| 0.60–0.74 | Moderate signal | Flag for research |
| < 0.60 | Low confidence | Hold, do not publish |

## What Must Never Be Published Without Human Verification
- Company financials derived from AI inference
- Executive names from unverified sources
- Procurement award values not confirmed by source URL
- Any quote attributed to a named individual
