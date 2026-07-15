# Architecture

YasinPress follows Clean Architecture. Outer adapters handle RSS, SQLite, HTTP-like routing, CLI, and publishers. Core services remain small, typed, and independently testable. Persistence is isolated behind repositories and transaction helpers; outbound delivery uses publisher protocols; AI behavior is hidden behind provider protocols.
