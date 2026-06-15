---
layout: default
title: "Identificador de fragmento de incrustaciones de documentos"
parent: "Spanish (Beta)"
---

# Identificador de fragmento de incrustaciones de documentos

> **Beta Translation:** This document was translated via Machine Learning and as such may not be 100% accurate. All non-English languages are currently classified as Beta.

## Resumen

Actualmente, el almacenamiento de incrustaciones de documentos almacena directamente el texto del fragmento en la carga útil de la base de datos vectorial, duplicando datos que existen en Garage. Esta especificación reemplaza el almacenamiento del texto del fragmento con referencias `chunk_id`.

## Estado actual

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

Carga útil del almacén de vectores:
```python
payload={"doc": chunk}  # Duplicates Garage content
```

## Diseño

### Cambios en el esquema

**ChunkEmbeddings** - reemplazar "chunk" con "chunk_id":
```python
@dataclass
class ChunkEmbeddings:
    chunk_id: str = ""
    vectors: list[list[float]] = field(default_factory=list)
```

**DocumentEmbeddingsResponse** - devolver `chunk_ids` en lugar de `chunks`:
```python
@dataclass
class DocumentEmbeddingsResponse:
    error: Error | None = None
    chunk_ids: list[str] = field(default_factory=list)
```

### Carga útil del almacén de vectores

Todos los almacenes (Qdrant, Milvus, Pinecone):
```python
payload={"chunk_id": chunk_id}
```

### Cambios en el Documento RAG

El procesador de documentos RAG recupera el contenido de los fragmentos de Garage:

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

### Cambios en la API/SDK

**DocumentEmbeddingsClient** devuelve chunk_ids:
```python
return resp.chunk_ids  # Changed from resp.chunks
```

**Formato de cable** (DocumentEmbeddingsResponseTranslator):
```python
result["chunk_ids"] = obj.chunk_ids  # Changed from chunks
```

### Cambios en la CLI

La herramienta de la CLI muestra los chunk_ids (los usuarios pueden obtener el contenido por separado si es necesario).

## Archivos a Modificar

### Esquema
`graphit-base/graphit/schema/knowledge/embeddings.py` - ChunkEmbeddings
`graphit-base/graphit/schema/services/query.py` - DocumentEmbeddingsResponse

### Mensajería/Traductores
`graphit-base/graphit/messaging/translators/embeddings_query.py` - DocumentEmbeddingsResponseTranslator

### Cliente
`graphit-base/graphit/base/document_embeddings_client.py` - return chunk_ids

### SDK/API de Python
`graphit-base/graphit/api/flow.py` - document_embeddings_query
`graphit-base/graphit/api/socket_client.py` - document_embeddings_query
`graphit-base/graphit/api/async_flow.py` - if applicable
`graphit-base/graphit/api/bulk_client.py` - import/export document embeddings
`graphit-base/graphit/api/async_bulk_client.py` - import/export document embeddings

### Servicio de Embeddings
`graphit-flow/graphit/embeddings/document_embeddings/embeddings.py` - pass chunk_id

### Escritores de Almacenamiento
`graphit-flow/graphit/storage/doc_embeddings/qdrant/write.py`
`graphit-flow/graphit/storage/doc_embeddings/milvus/write.py`
`graphit-flow/graphit/storage/doc_embeddings/pinecone/write.py`

### Servicios de Consulta
`graphit-flow/graphit/query/doc_embeddings/qdrant/service.py`
`graphit-flow/graphit/query/doc_embeddings/milvus/service.py`
`graphit-flow/graphit/query/doc_embeddings/pinecone/service.py`

### Gateway
`graphit-flow/graphit/gateway/dispatch/document_embeddings_query.py`
`graphit-flow/graphit/gateway/dispatch/document_embeddings_export.py`
`graphit-flow/graphit/gateway/dispatch/document_embeddings_import.py`

### Document RAG
`graphit-flow/graphit/retrieval/document_rag/rag.py` - add librarian client
`graphit-flow/graphit/retrieval/document_rag/document_rag.py` - fetch from Garage

### CLI
`graphit-cli/graphit/cli/invoke_document_embeddings.py`
`graphit-cli/graphit/cli/save_doc_embeds.py`
`graphit-cli/graphit/cli/load_doc_embeds.py`

## Beneficios

1. Única fuente de verdad: solo el texto de los chunks en Garage.
2. Almacenamiento de vectores reducido.
3. Permite el rastreo de origen en tiempo de consulta a través del chunk_id.
