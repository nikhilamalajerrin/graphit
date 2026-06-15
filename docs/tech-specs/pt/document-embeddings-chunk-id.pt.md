---
layout: default
title: "Incorporações de Documentos - ID do Trecho"
parent: "Portuguese (Beta)"
---

# Incorporações de Documentos - ID do Trecho

> **Beta Translation:** This document was translated via Machine Learning and as such may not be 100% accurate. All non-English languages are currently classified as Beta.

## Visão Geral

Atualmente, o armazenamento de incorporações de documentos armazena o texto do trecho diretamente no payload do armazenamento vetorial, duplicando dados que já existem no Garage. Esta especificação substitui o armazenamento do texto do trecho por referências `chunk_id`.

## Estado Atual

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

Payload do armazenamento vetorial:
```python
payload={"doc": chunk}  # Duplicates Garage content
```

## Design

### Schema Changes

**ChunkEmbeddings** - substituir "chunk" por "chunk_id":
```python
@dataclass
class ChunkEmbeddings:
    chunk_id: str = ""
    vectors: list[list[float]] = field(default_factory=list)
```

**DocumentEmbeddingsResponse** - retornar chunk_ids em vez de chunks:
```python
@dataclass
class DocumentEmbeddingsResponse:
    error: Error | None = None
    chunk_ids: list[str] = field(default_factory=list)
```

### Carga Útil do Armazenamento Vetorial

Todos os armazenamentos (Qdrant, Milvus, Pinecone):
```python
payload={"chunk_id": chunk_id}
```

### Alterações no Processador de Documentos RAG

O processador de documentos RAG busca o conteúdo dos fragmentos do Garage:

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

### Alterações na API/SDK

**DocumentEmbeddingsClient** retorna chunk_ids:
```python
return resp.chunk_ids  # Changed from resp.chunks
```

**Formato de dados** (DocumentEmbeddingsResponseTranslator):
```python
result["chunk_ids"] = obj.chunk_ids  # Changed from chunks
```

### Alterações na CLI

A ferramenta CLI exibe os chunk_ids (os chamadores podem buscar o conteúdo separadamente, se necessário).

## Arquivos a serem modificados

### Schema
`graphit-base/graphit/schema/knowledge/embeddings.py` - ChunkEmbeddings
`graphit-base/graphit/schema/services/query.py` - DocumentEmbeddingsResponse

### Mensagens/Tradutores
`graphit-base/graphit/messaging/translators/embeddings_query.py` - DocumentEmbeddingsResponseTranslator

### Cliente
`graphit-base/graphit/base/document_embeddings_client.py` - retornar chunk_ids

### SDK/API Python
`graphit-base/graphit/api/flow.py` - document_embeddings_query
`graphit-base/graphit/api/socket_client.py` - document_embeddings_query
`graphit-base/graphit/api/async_flow.py` - se aplicável
`graphit-base/graphit/api/bulk_client.py` - importar/exportar embeddings de documentos
`graphit-base/graphit/api/async_bulk_client.py` - importar/exportar embeddings de documentos

### Serviço de Embeddings
`graphit-flow/graphit/embeddings/document_embeddings/embeddings.py` - passar chunk_id

### Escritores de Armazenamento
`graphit-flow/graphit/storage/doc_embeddings/qdrant/write.py`
`graphit-flow/graphit/storage/doc_embeddings/milvus/write.py`
`graphit-flow/graphit/storage/doc_embeddings/pinecone/write.py`

### Serviços de Consulta
`graphit-flow/graphit/query/doc_embeddings/qdrant/service.py`
`graphit-flow/graphit/query/doc_embeddings/milvus/service.py`
`graphit-flow/graphit/query/doc_embeddings/pinecone/service.py`

### Gateway
`graphit-flow/graphit/gateway/dispatch/document_embeddings_query.py`
`graphit-flow/graphit/gateway/dispatch/document_embeddings_export.py`
`graphit-flow/graphit/gateway/dispatch/document_embeddings_import.py`

### Document RAG
`graphit-flow/graphit/retrieval/document_rag/rag.py` - adicionar cliente librarian
`graphit-flow/graphit/retrieval/document_rag/document_rag.py` - buscar do Garage

### CLI
`graphit-cli/graphit/cli/invoke_document_embeddings.py`
`graphit-cli/graphit/cli/save_doc_embeds.py`
`graphit-cli/graphit/cli/load_doc_embeds.py`

## Benefícios

1. Única fonte de verdade - texto do chunk apenas no Garage
2. Redução do armazenamento do vetor
3. Permite a rastreabilidade em tempo de consulta via chunk_id
