# YasinPress AI Contract

Status: Production architecture contract

## Boundary

AI is an optional intelligence layer behind a provider abstraction. Core pipeline behavior must remain deterministic and functional when AI is disabled, unavailable, rate-limited, or failing.

## Responsibilities

AI may provide:

- concise news rewrite/summary
- category classification
- priority/importance scoring
- breaking-news signal
- quality/completeness assistance

AI must not decide whether an article is eligible for publication when deterministic rules already reject it. In particular, the 12-hour freshness rule remains a core policy.

## Output state

Every article has an explicit AI state:

- `disabled`
- `pending`
- `rewritten`
- `fallback_original`
- `failed`

When AI rewrites content, the public message must contain the agreed `🤖` indicator.

## Fallback

If the AI provider fails, the pipeline may publish a validated original/locally generated summary according to configuration. AI failure must never crash RSS ingestion or the publisher worker.

## Provider isolation

Providers are selected through configuration/adapter interfaces. Provider-specific SDKs, authentication, retries, and response formats must not leak into domain models.

## Safety and quality

- Never invent facts not present in the source material.
- Preserve source attribution.
- Keep output concise enough for the configured channel limits.
- Do not reproduce the full source article.
- Do not log prompts containing secrets or provider credentials.
