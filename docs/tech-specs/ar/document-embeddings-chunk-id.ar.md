---
layout: default
title: "تضمينات المستندات - مُعرّف الجزء"
parent: "Arabic (Beta)"
---

# تضمينات المستندات - مُعرّف الجزء

> **Beta Translation:** This document was translated via Machine Learning and as such may not be 100% accurate. All non-English languages are currently classified as Beta.

## نظرة عامة

تخزين تضمينات المستندات يخزن حاليًا نص الجزء مباشرةً في حمولة مخزن المتجهات، مما يكرر البيانات الموجودة في Garage. يحل هذا المخطط تخزين نص الجزء باستخدام مراجع `chunk_id`.

## الحالة الحالية

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

حمولة تخزين المتجهات:
```python
payload={"doc": chunk}  # Duplicates Garage content
```

## التصميم

### تغييرات المخطط

**ChunkEmbeddings** - استبدال "chunk" بـ "chunk_id":
```python
@dataclass
class ChunkEmbeddings:
    chunk_id: str = ""
    vectors: list[list[float]] = field(default_factory=list)
```

**DocumentEmbeddingsResponse** - إرجاع معرفات الأجزاء (chunk_ids) بدلاً من الأجزاء نفسها:
```python
@dataclass
class DocumentEmbeddingsResponse:
    error: Error | None = None
    chunk_ids: list[str] = field(default_factory=list)
```

### حمولة مستودع المتجهات

جميع المستودعات (Qdrant، Milvus، Pinecone):
```python
payload={"chunk_id": chunk_id}
```

### التغييرات في معالج مستند RAG

يقوم معالج مستند RAG باسترداد محتوى الأجزاء من نظام Garage:

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

### التغييرات في واجهة برمجة التطبيقات (API) / مجموعة تطوير البرمجيات (SDK)

**DocumentEmbeddingsClient** تُرجع `chunk_ids`:
```python
return resp.chunk_ids  # Changed from resp.chunks
```

**تنسيق البيانات** (DocumentEmbeddingsResponseTranslator):
```python
result["chunk_ids"] = obj.chunk_ids  # Changed from chunks
```

### تغييرات واجهة سطر الأوامر (CLI)

تعرض أداة واجهة سطر الأوامر (CLI) معرفات الأجزاء (يمكن للمستخدمين استرداد المحتوى بشكل منفصل إذا لزم الأمر).

## الملفات التي يجب تعديلها

### المخطط (Schema)
`graphit-base/graphit/schema/knowledge/embeddings.py` - ChunkEmbeddings
`graphit-base/graphit/schema/services/query.py` - DocumentEmbeddingsResponse

### الرسائل/المترجمات
`graphit-base/graphit/messaging/translators/embeddings_query.py` - DocumentEmbeddingsResponseTranslator

### العميل (Client)
`graphit-base/graphit/base/document_embeddings_client.py` - إرجاع معرفات الأجزاء

### حزمة تطوير البرمجيات (SDK) / واجهة برمجة التطبيقات (API) بلغة بايثون
`graphit-base/graphit/api/flow.py` - document_embeddings_query
`graphit-base/graphit/api/socket_client.py` - document_embeddings_query
`graphit-base/graphit/api/async_flow.py` - إذا كان ذلك ممكنًا
`graphit-base/graphit/api/bulk_client.py` - استيراد/تصدير تضمينات المستندات
`graphit-base/graphit/api/async_bulk_client.py` - استيراد/تصدير تضمينات المستندات

### خدمة التضمينات
`graphit-flow/graphit/embeddings/document_embeddings/embeddings.py` - تمرير معرف الجزء

### أدوات الكتابة في التخزين
`graphit-flow/graphit/storage/doc_embeddings/qdrant/write.py`
`graphit-flow/graphit/storage/doc_embeddings/milvus/write.py`
`graphit-flow/graphit/storage/doc_embeddings/pinecone/write.py`

### خدمات الاستعلام
`graphit-flow/graphit/query/doc_embeddings/qdrant/service.py`
`graphit-flow/graphit/query/doc_embeddings/milvus/service.py`
`graphit-flow/graphit/query/doc_embeddings/pinecone/service.py`

### البوابة (Gateway)
`graphit-flow/graphit/gateway/dispatch/document_embeddings_query.py`
`graphit-flow/graphit/gateway/dispatch/document_embeddings_export.py`
`graphit-flow/graphit/gateway/dispatch/document_embeddings_import.py`

### استرجاع المعلومات من المستندات (Document RAG)
`graphit-flow/graphit/retrieval/document_rag/rag.py` - إضافة عميل أمين المكتبة
`graphit-flow/graphit/retrieval/document_rag/document_rag.py` - الاسترداد من Garage

### واجهة سطر الأوامر (CLI)
`graphit-cli/graphit/cli/invoke_document_embeddings.py`
`graphit-cli/graphit/cli/save_doc_embeds.py`
`graphit-cli/graphit/cli/load_doc_embeds.py`

## الفوائد

1. مصدر واحد للحقيقة - نص الأجزاء فقط في Garage
2. تقليل مساحة التخزين في مخزن المتجهات
3. يتيح تتبع مصدر المعلومات في وقت الاستعلام عبر معرف الجزء.
