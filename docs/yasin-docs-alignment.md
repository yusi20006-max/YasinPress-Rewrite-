# YASIN-DOCS Alignment

YasinPress is treated as the specialized Persian-news publishing engine described by the canonical Yasin ecosystem architecture.

## Boundary

YasinPress owns its application pipeline and local SQLite state. YasinHub/YasinCLI remain responsible for ecosystem lifecycle and operations.

## Publishing

Channel-specific publishing remains project-owned. The canonical publisher contract is local to YasinPress; no dependency on Yasin-AI is assumed without source-level evidence.

## Ecosystem relationship

```text
YasinCLI → YasinHub → YasinPress
                         ├─ News Pipeline
                         ├─ Content Processing
                         └─ Publishing
```

## Evidence policy

This document records only relationships supported by the canonical YASIN-DOCS architecture and the YasinPress implementation. Future shared Feed/Press components remain a proposal, not a dependency.
