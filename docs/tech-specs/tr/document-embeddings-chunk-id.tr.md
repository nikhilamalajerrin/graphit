---
layout: default
title: "Belge Gömme Parçası Kimliği"
parent: "Turkish (Beta)"
---

# Belge Gömme Parçası Kimliği

> **Beta Translation:** This document was translated via Machine Learning and as such may not be 100% accurate. All non-English languages are currently classified as Beta.

## Genel Bakış

Belge gömme depolaması şu anda parça metnini doğrudan vektör deposu yüküne kaydederek, Garage'da bulunan verilerin çoğaltılmasına neden oluyor. Bu özellik, parça metni depolamasını `chunk_id` referanslarıyla değiştirmektedir.

## Mevcut Durum

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

Vektör depolama yükü:
```python
payload={"doc": chunk}  # Duplicates Garage content
```

## Tasarım

### Şema Değişiklikleri

**ChunkEmbeddings** - chunk'ı chunk_id ile değiştirin:
```python
@dataclass
class ChunkEmbeddings:
    chunk_id: str = ""
    vectors: list[list[float]] = field(default_factory=list)
```

**DocumentEmbeddingsResponse** - parçalar yerine chunk_id'leri döndür:
```python
@dataclass
class DocumentEmbeddingsResponse:
    error: Error | None = None
    chunk_ids: list[str] = field(default_factory=list)
```

### Vektör Depolama Veri Yapısı

Tüm depolar (Qdrant, Milvus, Pinecone):
```python
payload={"chunk_id": chunk_id}
```

### Belge RAG Değişiklikleri

Belge RAG işlemcisi, parça içeriğini Garage'dan alır:

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

### API/SDK Değişiklikleri

**DocumentEmbeddingsClient**, `chunk_ids` değerini döndürür:
```python
return resp.chunk_ids  # Changed from resp.chunks
```

**Kablolu format** (DocumentEmbeddingsResponseTranslator):
```python
result["chunk_ids"] = obj.chunk_ids  # Changed from chunks
```

### CLI Değişiklikleri

CLI aracı, chunk_id'leri gösterir (çağrıcılar, gerekirse içeriği ayrı olarak alabilir).

## Değiştirilecek Dosyalar

### Şema
`graphit-base/graphit/schema/knowledge/embeddings.py` - ChunkEmbeddings
`graphit-base/graphit/schema/services/query.py` - DocumentEmbeddingsResponse

### Mesajlaşma/Çeviriciler
`graphit-base/graphit/messaging/translators/embeddings_query.py` - DocumentEmbeddingsResponseTranslator

### İstemci
`graphit-base/graphit/base/document_embeddings_client.py` - chunk_id'leri döndür

### Python SDK/API
`graphit-base/graphit/api/flow.py` - document_embeddings_query
`graphit-base/graphit/api/socket_client.py` - document_embeddings_query
`graphit-base/graphit/api/async_flow.py` - eğer uygunsa
`graphit-base/graphit/api/bulk_client.py` - belge gömülerinin içe/dışa aktarımı
`graphit-base/graphit/api/async_bulk_client.py` - belge gömülerinin içe/dışa aktarımı

### Gömme Hizmeti
`graphit-flow/graphit/embeddings/document_embeddings/embeddings.py` - chunk_id'yi ilet

### Depolama Yazıcıları
`graphit-flow/graphit/storage/doc_embeddings/qdrant/write.py`
`graphit-flow/graphit/storage/doc_embeddings/milvus/write.py`
`graphit-flow/graphit/storage/doc_embeddings/pinecone/write.py`

### Sorgu Hizmetleri
`graphit-flow/graphit/query/doc_embeddings/qdrant/service.py`
`graphit-flow/graphit/query/doc_embeddings/milvus/service.py`
`graphit-flow/graphit/query/doc_embeddings/pinecone/service.py`

### Ağ Geçidi
`graphit-flow/graphit/gateway/dispatch/document_embeddings_query.py`
`graphit-flow/graphit/gateway/dispatch/document_embeddings_export.py`
`graphit-flow/graphit/gateway/dispatch/document_embeddings_import.py`

### Belge RAG
`graphit-flow/graphit/retrieval/document_rag/rag.py` - librarian istemcisini ekle
`graphit-flow/graphit/retrieval/document_rag/document_rag.py` - Garage'dan al

### CLI
`graphit-cli/graphit/cli/invoke_document_embeddings.py`
`graphit-cli/graphit/cli/save_doc_embeds.py`
`graphit-cli/graphit/cli/load_doc_embeds.py`

## Faydalar

1. Tek kaynaklı doğruluk - chunk metni yalnızca Garage'da bulunur.
2. Vektör depolama alanında azalma.
3. chunk_id aracılığıyla sorgu zamanı köken bilgisini sağlar.
