# YasinPress Rewrite 1.0.0

YasinPress Rewrite 1.0.0 delivers a complete Python 3.13 foundation for automated news aggregation and publication. The release includes typed modules, documentation, tests, operational helpers, and a command-line entrypoint suitable for production hardening and extension.

## Verification

- Import smoke test passes.
- Processing, cache, scheduler, API, and categorization tests pass.
- Package sources compile successfully.
- Fresh Termux installation was verified on Python 3.14.6.
- 114 tests passed in the verified Termux run.
- BBC Persian RSS endpoint returned HTTP 200 with valid XML.

## Post-1.0.0 hardening

The following maintenance changes are now part of the 1.0.0 line:

- Worker jobs retain handler results for runtime reporting.
- Runtime execution no longer relies on an invalid `job.state` attribute.
- PWA JSON Feed output now carries Persian language metadata and article provenance.
- AI-modified PWA items expose `date_modified`.
- RSS output now includes language, latest build time, and source metadata.
- PWA and RSS persistence remain atomic through temporary-file replacement.
- Existing feed items are de-duplicated before a new article is inserted.

## Pending live verification

- Fresh end-to-end `yasinpress run` after the runtime fixes.
- Eitaa publishing with a newly issued credential after the previous token was revoked.
- Production AI provider execution.
- Deployed PWA/RSS hosting.
