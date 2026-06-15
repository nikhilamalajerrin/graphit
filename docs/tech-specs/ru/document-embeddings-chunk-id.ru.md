---
layout: default
title: "Идентификатор фрагмента встраиваний документов"
parent: "Russian (Beta)"
---

# Идентификатор фрагмента встраиваний документов

> **Beta Translation:** This document was translated via Machine Learning and as such may not be 100% accurate. All non-English languages are currently classified as Beta.

## Обзор

В настоящее время хранилище встраиваний документов хранит текст фрагментов непосредственно в полезной нагрузке векторного хранилища, дублируя данные, которые существуют в Garage. Данная спецификация заменяет хранение текста фрагментов ссылками на `chunk_id`.

## Текущее состояние

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

Структура данных для хранения векторов:
```python
payload={"doc": chunk}  # Duplicates Garage content
```

## Дизайн

### Изменения схемы

**ChunkEmbeddings** - заменить "chunk" на "chunk_id":
```python
@dataclass
class ChunkEmbeddings:
    chunk_id: str = ""
    vectors: list[list[float]] = field(default_factory=list)
```

**DocumentEmbeddingsResponse** - возвращать chunk_ids вместо фрагментов:
```python
@dataclass
class DocumentEmbeddingsResponse:
    error: Error | None = None
    chunk_ids: list[str] = field(default_factory=list)
```

### Структура данных для векторного хранилища

Все хранилища (Qdrant, Milvus, Pinecone):
```python
payload={"chunk_id": chunk_id}
```

### Изменения в системе извлечения информации (RAG)

Модуль обработки документов RAG извлекает содержимое фрагментов из системы Garage:

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

### Изменения API/SDK

**DocumentEmbeddingsClient** возвращает chunk_ids:
```python
return resp.chunk_ids  # Changed from resp.chunks
```

**Формат данных** (DocumentEmbeddingsResponseTranslator):
```python
result["chunk_ids"] = obj.chunk_ids  # Changed from chunks
```

### Изменения в CLI

Инструмент CLI отображает идентификаторы фрагментов (пользователи могут извлекать контент отдельно, если это необходимо).

## Файлы для изменения

### Схема
`graphit-base/graphit/schema/knowledge/embeddings.py` - ChunkEmbeddings
`graphit-base/graphit/schema/services/query.py` - DocumentEmbeddingsResponse

### Сообщения/Переводчики
`graphit-base/graphit/messaging/translators/embeddings_query.py` - DocumentEmbeddingsResponseTranslator

### Клиент
`graphit-base/graphit/base/document_embeddings_client.py` - возвращать идентификаторы фрагментов

### Python SDK/API
`graphit-base/graphit/api/flow.py` - document_embeddings_query
`graphit-base/graphit/api/socket_client.py` - document_embeddings_query
`graphit-base/graphit/api/async_flow.py` - если применимо
`graphit-base/graphit/api/bulk_client.py` - импорт/экспорт векторных представлений документов
`graphit-base/graphit/api/async_bulk_client.py` - импорт/экспорт векторных представлений документов

### Сервис векторных представлений
`graphit-flow/graphit/embeddings/document_embeddings/embeddings.py` - передавать идентификатор фрагмента

### Модули записи в хранилище
`graphit-flow/graphit/storage/doc_embeddings/qdrant/write.py`
`graphit-flow/graphit/storage/doc_embeddings/milvus/write.py`
`graphit-flow/graphit/storage/doc_embeddings/pinecone/write.py`

### Сервисы запросов
`graphit-flow/graphit/query/doc_embeddings/qdrant/service.py`
`graphit-flow/graphit/query/doc_embeddings/milvus/service.py`
`graphit-flow/graphit/query/doc_embeddings/pinecone/service.py`

### Шлюз
`graphit-flow/graphit/gateway/dispatch/document_embeddings_query.py`
`graphit-flow/graphit/gateway/dispatch/document_embeddings_export.py`
`graphit-flow/graphit/gateway/dispatch/document_embeddings_import.py`

### Document RAG
`graphit-flow/graphit/retrieval/document_rag/rag.py` - добавить клиент librarian
`graphit-flow/graphit/retrieval/document_rag/document_rag.py` - извлекать из Garage

### CLI
`graphit-cli/graphit/cli/invoke_document_embeddings.py`
`graphit-cli/graphit/cli/save_doc_embeds.py`
`graphit-cli/graphit/cli/load_doc_embeds.py`

## Преимущества

1. Единый источник истины - текст фрагментов только в Garage
2. Уменьшение объема хранимых векторных представлений
3. Обеспечивает отслеживание происхождения данных в момент запроса с помощью идентификатора фрагмента.
