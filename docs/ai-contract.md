# YasinPress AI Contract

Status: Production architecture contract

## Boundary

AI is an optional intelligence layer behind a provider abstraction. Core pipeline behavior must remain deterministic and functional when AI is disabled, unavailable, rate-limited, or failing.

The canonical provider is **Yasin-AI v1.1.4**. YasinPress consumes its public generation contracts and facade only; it does not import provider SDKs or private Yasin-AI modules.

## Responsibilities

AI may provide:

- concise news rewrite/summary
- category classification
- priority/importance scoring
- breaking-news signal
- quality/completeness assistance

AI must not decide whether an article is eligible for publication when deterministic rules already reject it. In particular, the 12-hour freshness rule remains a core policy.

## Canonical integration

YasinPress uses:

- `yasinai.contracts.generation.GenerationRequest`
- `yasinai.contracts.generation.GenerationResult`
- `yasinai.services.generation_service.GenerationService`

The adapter translates these contracts into the existing YasinPress `AIProvider` boundary. Provider routing, credentials, retries and provider-specific behavior remain owned by Yasin-AI.

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

Structured AI responses are validated before they affect an article. Invalid responses are treated as AI failures and preserve the original article.

## Provider isolation

Providers are selected through configuration/adapter interfaces. Provider-specific SDKs, authentication, retries, and response formats must not leak into domain models.

Legacy OpenAI-compatible operation remains available only through the explicit `openai-compatible` provider setting; it is not the canonical integration path.

## Safety and quality

- Never invent facts not present in the source material.
- Preserve source attribution.
- Keep output concise enough for the configured channel limits.
- Do not reproduce the full source article.
- Do not log prompts containing secrets or provider credentials.
- AI failure or malformed output must not corrupt queue, scheduler or publishing state.
