---
layout: default
title: "Kitambulisho cha Sehemu ya Matini (Document Embeddings Chunk ID)"
parent: "Swahili (Beta)"
---

# Kitambulisho cha Sehemu ya Matini (Document Embeddings Chunk ID)

> **Beta Translation:** This document was translated via Machine Learning and as such may not be 100% accurate. All non-English languages are currently classified as Beta.

## Muhtasari

Hifadhi ya matini ya maandishi kwa sasa huhifadhi matini ya sehemu moja kwa moja katika sehemu ya data ya hifadhi ya vector, na hivyo kurudia data ambayo ipo katika Garage. Hati hii inabadilisha uhifadhi wa matini ya sehemu kwa kutumia marejeleo ya `chunk_id`.

## Hali ya Sasa

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

Hifadhi ya data ya aina ya vector:
```python
payload={"doc": chunk}  # Duplicates Garage content
```

## Ubunifu

### Mabadiliko ya Mpango

**ChunkEmbeddings** - badilisha "chunk" na "chunk_id":
```python
@dataclass
class ChunkEmbeddings:
    chunk_id: str = ""
    vectors: list[list[float]] = field(default_factory=list)
```

**Jibu la DocumentEmbeddingsResponse** - irudishe `chunk_ids` badala ya `chunks`:
```python
@dataclass
class DocumentEmbeddingsResponse:
    error: Error | None = None
    chunk_ids: list[str] = field(default_factory=list)
```

### Mfumo wa Hifadhi ya Vektor

Maduka yote (Qdrant, Milvus, Pinecone):
```python
payload={"chunk_id": chunk_id}
```

### Mabadiliko ya Mchakato wa RAG wa Hati

Mchakato wa RAG wa hati hupata maudhui ya sehemu kutoka kwa Garage:

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

### Mabadiliko ya API/SDK

**DocumentEmbeddingsClient** hurudia chunk_ids:
```python
return resp.chunk_ids  # Changed from resp.chunks
```

**Muundo wa data** (Mfasiri wa Majibu ya Matangazo ya Hati):
```python
result["chunk_ids"] = obj.chunk_ids  # Changed from chunks
```

### Mabadiliko ya CLI

Zana ya CLI inaonyesha kitambulisho cha vipande (watumiaji wanaweza kupata maudhui kando ikiwa ni lazima).

## Faili Zinazohitajika Kubadilishwa

### Mpango (Schema)
`graphit-base/graphit/schema/knowledge/embeddings.py` - ChunkEmbeddings
`graphit-base/graphit/schema/services/query.py` - DocumentEmbeddingsResponse

### Ujumbe/Watafsiri
`graphit-base/graphit/messaging/translators/embeddings_query.py` - DocumentEmbeddingsResponseTranslator

### Mteja (Client)
`graphit-base/graphit/base/document_embeddings_client.py` - rudisha kitambulisho cha vipande

### SDK/API ya Python
`graphit-base/graphit/api/flow.py` - document_embeddings_query
`graphit-base/graphit/api/socket_client.py` - document_embeddings_query
`graphit-base/graphit/api/async_flow.py` - ikiwa inafaa
`graphit-base/graphit/api/bulk_client.py` - uagizaji/uangamizi wa vipande vya maandishi
`graphit-base/graphit/api/async_bulk_client.py` - uagizaji/uangamizi wa vipande vya maandishi

### Huduma ya Vipande vya Maandishi (Embeddings Service)
`graphit-flow/graphit/embeddings/document_embeddings/embeddings.py` - pitisha kitambulisho cha kipande

### Waandishi wa Uhifadhi (Storage Writers)
`graphit-flow/graphit/storage/doc_embeddings/qdrant/write.py`
`graphit-flow/graphit/storage/doc_embeddings/milvus/write.py`
`graphit-flow/graphit/storage/doc_embeddings/pinecone/write.py`

### Huduma za Utafutaji (Query Services)
`graphit-flow/graphit/query/doc_embeddings/qdrant/service.py`
`graphit-flow/graphit/query/doc_embeddings/milvus/service.py`
`graphit-flow/graphit/query/doc_embeddings/pinecone/service.py`

### Lango (Gateway)
`graphit-flow/graphit/gateway/dispatch/document_embeddings_query.py`
`graphit-flow/graphit/gateway/dispatch/document_embeddings_export.py`
`graphit-flow/graphit/gateway/dispatch/document_embeddings_import.py`

### Utafutaji wa Hati (Document RAG)
`graphit-flow/graphit/retrieval/document_rag/rag.py` - ongeza mteja wa "librarian"
`graphit-flow/graphit/retrieval/document_rag/document_rag.py` - pata kutoka "Garage"

### CLI
`graphit-cli/graphit/cli/invoke_document_embeddings.py`
`graphit-cli/graphit/cli/save_doc_embeds.py`
`graphit-cli/graphit/cli/load_doc_embeds.py`

## Faida

1. Chanzo kimoja cha ukweli - maandishi ya vipande tu katika "Garage"
2. Kupunguzwa kwa uhifadhi wa hifadhi ya vector
3. Inawezesha uhakikisho wa muda wa utafutaji kupitia kitambulisho cha kipande.
