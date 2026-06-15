---
layout: default
title: "Document Embeddings Chunk ID"
parent: "Tech Specs"
---

# Document Embeddings Chunk ID

## Overview

Document embeddings storage currently stores chunk text directly in the vector store payload, duplicating data that exists in Garage. This spec replaces chunk text storage with `chunk_id` references.

## Current State

```python
@dataclass
class ChunkEmbeddings:
    chunk: bytes = b""
    vectors: list[list[float]] = field(default_factory=list)

@dataclass
class DocumentEmbeddingsResponse:
    error: Error | None = None
    chunks: list[str] = field(default_factory=list)
```

Vector store payload:
```python
payload={"doc": chunk}  # Duplicates Garage content
```

## Design

### Schema Changes

**ChunkEmbeddings** - replace chunk with chunk_id:
```python
@dataclass
class ChunkEmbeddings:
    chunk_id: str = ""
    vectors: list[list[float]] = field(default_factory=list)
```

**DocumentEmbeddingsResponse** - return chunk_ids instead of chunks:
```python
@dataclass
class DocumentEmbeddingsResponse:
    error: Error | None = None
    chunk_ids: list[str] = field(default_factory=list)
```

### Vector Store Payload

All stores (Qdrant, Milvus, Pinecone):
```python
payload={"chunk_id": chunk_id}
```

### Document RAG Changes

The document RAG processor fetches chunk content from Garage:

```python
# Get chunk_ids from embeddings store
chunk_ids = await self.rag.doc_embeddings_client.query(...)

# Fetch chunk content from Garage
docs = []
for chunk_id in chunk_ids:
    content = await self.rag.librarian_client.get_document_content(
        chunk_id, self.user
    )
    docs.append(content)
```

### API/SDK Changes

**DocumentEmbeddingsClient** returns chunk_ids:
```python
return resp.chunk_ids  # Changed from resp.chunks
```

**Wire format** (DocumentEmbeddingsResponseTranslator):
```python
result["chunk_ids"] = obj.chunk_ids  # Changed from chunks
```

### CLI Changes

CLI tool displays chunk_ids (callers can fetch content separately if needed).

## Files to Modify

### Schema
- `graphit-base/graphit/schema/knowledge/embeddings.py` - ChunkEmbeddings
- `graphit-base/graphit/schema/services/query.py` - DocumentEmbeddingsResponse

### Messaging/Translators
- `graphit-base/graphit/messaging/translators/embeddings_query.py` - DocumentEmbeddingsResponseTranslator

### Client
- `graphit-base/graphit/base/document_embeddings_client.py` - return chunk_ids

### Python SDK/API
- `graphit-base/graphit/api/flow.py` - document_embeddings_query
- `graphit-base/graphit/api/socket_client.py` - document_embeddings_query
- `graphit-base/graphit/api/async_flow.py` - if applicable
- `graphit-base/graphit/api/bulk_client.py` - import/export document embeddings
- `graphit-base/graphit/api/async_bulk_client.py` - import/export document embeddings

### Embeddings Service
- `graphit-flow/graphit/embeddings/document_embeddings/embeddings.py` - pass chunk_id

### Storage Writers
- `graphit-flow/graphit/storage/doc_embeddings/qdrant/write.py`
- `graphit-flow/graphit/storage/doc_embeddings/milvus/write.py`
- `graphit-flow/graphit/storage/doc_embeddings/pinecone/write.py`

### Query Services
- `graphit-flow/graphit/query/doc_embeddings/qdrant/service.py`
- `graphit-flow/graphit/query/doc_embeddings/milvus/service.py`
- `graphit-flow/graphit/query/doc_embeddings/pinecone/service.py`

### Gateway
- `graphit-flow/graphit/gateway/dispatch/document_embeddings_query.py`
- `graphit-flow/graphit/gateway/dispatch/document_embeddings_export.py`
- `graphit-flow/graphit/gateway/dispatch/document_embeddings_import.py`

### Document RAG
- `graphit-flow/graphit/retrieval/document_rag/rag.py` - add librarian client
- `graphit-flow/graphit/retrieval/document_rag/document_rag.py` - fetch from Garage

### CLI
- `graphit-cli/graphit/cli/invoke_document_embeddings.py`
- `graphit-cli/graphit/cli/save_doc_embeds.py`
- `graphit-cli/graphit/cli/load_doc_embeds.py`

## Benefits

1. Single source of truth - chunk text only in Garage
2. Reduced vector store storage
3. Enables query-time provenance via chunk_id
