# Final Gate Note

The production Eitaa renderer intentionally marks a breaking article only when the title contains a configured severe-event signal and the publication timestamp is within the 12-hour breaking-news window. Regression tests must therefore use a dynamically fresh timestamp for breaking cases; fixed historical timestamps are valid for deterministic normal-message layout tests but must not be used to assert current breaking status.
