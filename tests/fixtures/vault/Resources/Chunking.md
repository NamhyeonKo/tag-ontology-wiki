---
description: "Splitting documents at meaningful boundaries for retrieval."
type: resource
category:
  - ai/rag
tags:
  - information-retrieval
---
# Chunking

## Semantic chunking

Semantic chunking splits a document where its topic changes, keeping related sentences together.
It aims to make each retrieved unit meaningful without unrelated surrounding material.

## Tradeoffs

Small chunks improve precision but may lose context. Large chunks preserve context but include irrelevant text.
BM25 is a possible downstream ranker; ranking is outside this note's scope.
