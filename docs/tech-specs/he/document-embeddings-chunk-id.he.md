---
layout: default
title: "מזהה מקטע של הטמעות מסמכים"
parent: "Hebrew (Beta)"
---

# מזהה מקטע של הטמעות מסמכים

> **Beta Translation:** This document was translated via Machine Learning and as such may not be 100% accurate. All non-English languages are currently classified as Beta.

## סקירה כללית

אחסון הטמעות מסמכים מאחסן כרגע את הטקסט של המקטעים ישירות בתוך מטען ה-vector store, מה שמשכפל נתונים הקיימים ב-Garage. מפרט זה מחליף את אחסון הטקסט של המקטעים עם הפניות ל-`chunk_id`.

## מצב נוכחי

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

מטען אחסון וקטורים:
```python
payload={"doc": chunk}  # Duplicates Garage content
```

## עיצוב

### שינויים בסכימה

**ChunkEmbeddings** - החלפת "chunk" ב-"chunk_id":
```python
@dataclass
class ChunkEmbeddings:
    chunk_id: str = ""
    vectors: list[list[float]] = field(default_factory=list)
```

**תגובת DocumentEmbeddingsResponse** - החזרת מזהי חלקים (chunk_ids) במקום חלקים (chunks):
```python
@dataclass
class DocumentEmbeddingsResponse:
    error: Error | None = None
    chunk_ids: list[str] = field(default_factory=list)
```

### מטען של אחסון וקטורים

כל האחסונים (Qdrant, Milvus, Pinecone):
```python
payload={"chunk_id": chunk_id}
```

### שינויים במסמך RAG

מעבד מסמכי ה-RAG שולף תוכן מקטעים מ-Garage:

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

### שינויים ב-API/SDK

**DocumentEmbeddingsClient** מחזיר את chunk_ids:
```python
return resp.chunk_ids  # Changed from resp.chunks
```

**פורמט של נתונים** (DocumentEmbeddingsResponseTranslator):
```python
result["chunk_ids"] = obj.chunk_ids  # Changed from chunks
```

### שינויים בממשק שורת הפקודה (CLI)

כלי ה-CLI מציג מזהי חלקים (chunk_ids) (המשתמשים יכולים לשלוף את התוכן בנפרד אם יש צורך).

## קבצים לשינוי

### סכימה (Schema)
`graphit-base/graphit/schema/knowledge/embeddings.py` - ChunkEmbeddings
`graphit-base/graphit/schema/services/query.py` - DocumentEmbeddingsResponse

### הודעות/מתרגמים
`graphit-base/graphit/messaging/translators/embeddings_query.py` - DocumentEmbeddingsResponseTranslator

### לקוח (Client)
`graphit-base/graphit/base/document_embeddings_client.py` - החזרת מזהי חלקים (chunk_ids)

### ערכת פיתוח תוכנה (SDK) / API בפייתון
`graphit-base/graphit/api/flow.py` - document_embeddings_query
`graphit-base/graphit/api/socket_client.py` - document_embeddings_query
`graphit-base/graphit/api/async_flow.py` - אם רלוונטי
`graphit-base/graphit/api/bulk_client.py` - ייבוא/ייצוא של הטמעות מסמכים (document embeddings)
`graphit-base/graphit/api/async_bulk_client.py` - ייבוא/ייצוא של הטמעות מסמכים (document embeddings)

### שירות הטמעות
`graphit-flow/graphit/embeddings/document_embeddings/embeddings.py` - העברת מזהה חלק (chunk_id)

### כותבי אחסון
`graphit-flow/graphit/storage/doc_embeddings/qdrant/write.py`
`graphit-flow/graphit/storage/doc_embeddings/milvus/write.py`
`graphit-flow/graphit/storage/doc_embeddings/pinecone/write.py`

### שירותי שאילתות
`graphit-flow/graphit/query/doc_embeddings/qdrant/service.py`
`graphit-flow/graphit/query/doc_embeddings/milvus/service.py`
`graphit-flow/graphit/query/doc_embeddings/pinecone/service.py`

### שער (Gateway)
`graphit-flow/graphit/gateway/dispatch/document_embeddings_query.py`
`graphit-flow/graphit/gateway/dispatch/document_embeddings_export.py`
`graphit-flow/graphit/gateway/dispatch/document_embeddings_import.py`

### אחזור מידע ממסמכים (Document RAG)
`graphit-flow/graphit/retrieval/document_rag/rag.py` - הוספת לקוח של "ספרן" (librarian)
`graphit-flow/graphit/retrieval/document_rag/document_rag.py` - שליפה מ-"Garage"

### ממשק שורת הפקודה (CLI)
`graphit-cli/graphit/cli/invoke_document_embeddings.py`
`graphit-cli/graphit/cli/save_doc_embeds.py`
`graphit-cli/graphit/cli/load_doc_embeds.py`

## יתרונות

1. מקור יחיד לאמת - טקסט החלקים נמצא רק ב-"Garage".
2. הפחתת נפח האחסון של מאגר הווקטורים.
3. מאפשר מעקב אחר מקור המידע בזמן השאילתה באמצעות מזהה החלק (chunk_id).
