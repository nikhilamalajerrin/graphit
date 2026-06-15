---
layout: default
title: "Объяснимость работы агента: Регистрация происхождения"
parent: "Russian (Beta)"
---

# Объяснимость работы агента: Регистрация происхождения

> **Beta Translation:** This document was translated via Machine Learning and as such may not be 100% accurate. All non-English languages are currently classified as Beta.

## Обзор

Добавьте регистрацию происхождения в цикл работы агента React, чтобы сеансы работы агента можно было отслеживать и отлаживать с использованием той же инфраструктуры объяснимости, что и в GraphRAG.

**Принятые решения:**
Запись в `urn:graph:retrieval` (общий граф объяснимости)
Линейная цепочка зависимостей на данный момент (анализ N → был получен из → анализ N-1)
Инструменты являются непрозрачными "черными ящиками" (записывайте только входные и выходные данные)
Поддержка DAG отложена до будущей итерации

## Типы сущностей

И GraphRAG, и Agent используют PROV-O в качестве базовой онтологии с подтипами, специфичными для GraphIt:

### Типы GraphRAG
| Сущность | Тип PROV-O | Типы TG | Описание |
|--------|-------------|----------|-------------|
| Вопрос | `prov:Activity` | `tg:Question`, `tg:GraphRagQuestion` | Запрос пользователя |
| Исследование | `prov:Entity` | `tg:Exploration` | Ряды, извлеченные из графа знаний |
| Фокус | `prov:Entity` | `tg:Focus` | Выбранные ряды с обоснованием |
| Синтез | `prov:Entity` | `tg:Synthesis` | Окончательный ответ |

### Типы Agent
| Сущность | Тип PROV-O | Типы TG | Описание |
|--------|-------------|----------|-------------|
| Вопрос | `prov:Activity` | `tg:Question`, `tg:AgentQuestion` | Запрос пользователя |
| Анализ | `prov:Entity` | `tg:Analysis` | Каждый цикл "думай/действуй/наблюдай" |
| Вывод | `prov:Entity` | `tg:Conclusion` | Окончательный ответ |

### Типы Document RAG
| Сущность | Тип PROV-O | Типы TG | Описание |
|--------|-------------|----------|-------------|
| Вопрос | `prov:Activity` | `tg:Question`, `tg:DocRagQuestion` | Запрос пользователя |
| Исследование | `prov:Entity` | `tg:Exploration` | Части, извлеченные из хранилища документов |
| Синтез | `prov:Entity` | `tg:Synthesis` | Окончательный ответ |

**Примечание:** Document RAG использует подмножество типов GraphRAG (нет этапа "Фокус", поскольку нет этапа выбора/обоснования ребер).

### Подтипы вопросов

Все сущности "Вопрос" имеют `tg:Question` в качестве базового типа, но имеют определенный подтип для идентификации механизма извлечения:

| Подтип | Шаблон URI | Механизм |
|---------|-------------|-----------|
| `tg:GraphRagQuestion` | `urn:graphit:question:{uuid}` | RAG на основе графа знаний |
| `tg:DocRagQuestion` | `urn:graphit:docrag:{uuid}` | RAG на основе документов/частей |
| `tg:AgentQuestion` | `urn:graphit:agent:{uuid}` | Агент ReAct |

Это позволяет запрашивать все вопросы через `tg:Question`, одновременно фильтруя по конкретному механизму с помощью подтипа.

## Модель происхождения

```
Question (urn:graphit:agent:{uuid})
    │
    │  tg:query = "User's question"
    │  prov:startedAtTime = timestamp
    │  rdf:type = prov:Activity, tg:Question
    │
    ↓ prov:wasDerivedFrom
    │
Analysis1 (urn:graphit:agent:{uuid}/i1)
    │
    │  tg:thought = "I need to query the knowledge base..."
    │  tg:action = "knowledge-query"
    │  tg:arguments = {"question": "..."}
    │  tg:observation = "Result from tool..."
    │  rdf:type = prov:Entity, tg:Analysis
    │
    ↓ prov:wasDerivedFrom
    │
Analysis2 (urn:graphit:agent:{uuid}/i2)
    │  ...
    ↓ prov:wasDerivedFrom
    │
Conclusion (urn:graphit:agent:{uuid}/final)
    │
    │  tg:answer = "The final response..."
    │  rdf:type = prov:Entity, tg:Conclusion
```

### Модель происхождения документов RAG

```
Question (urn:graphit:docrag:{uuid})
    │
    │  tg:query = "User's question"
    │  prov:startedAtTime = timestamp
    │  rdf:type = prov:Activity, tg:Question
    │
    ↓ prov:wasGeneratedBy
    │
Exploration (urn:graphit:docrag:{uuid}/exploration)
    │
    │  tg:chunkCount = 5
    │  tg:selectedChunk = "chunk-id-1"
    │  tg:selectedChunk = "chunk-id-2"
    │  ...
    │  rdf:type = prov:Entity, tg:Exploration
    │
    ↓ prov:wasDerivedFrom
    │
Synthesis (urn:graphit:docrag:{uuid}/synthesis)
    │
    │  tg:content = "The synthesized answer..."
    │  rdf:type = prov:Entity, tg:Synthesis
```

## Необходимые изменения

### 1. Изменения схемы

**Файл:** `graphit-base/graphit/schema/services/agent.py`

Добавить поля `session_id` и `collection` в `AgentRequest`:
```python
@dataclass
class AgentRequest:
    question: str = ""
    state: str = ""
    group: list[str] | None = None
    history: list[AgentStep] = field(default_factory=list)
    user: str = ""
    collection: str = "default"  # NEW: Collection for provenance traces
    streaming: bool = False
    session_id: str = ""         # NEW: For provenance tracking across iterations
```

**Файл:** `graphit-base/graphit/messaging/translators/agent.py`

Обновить переводчик для обработки `session_id` и `collection` как в `to_pulsar()`, так и в `from_pulsar()`.

### 2. Добавить компонент "Explainability Producer" в сервис Agent

**Файл:** `graphit-flow/graphit/agent/react/service.py`

Зарегистрировать компонент "explainability" (в соответствии с тем же шаблоном, что и GraphRAG):
```python
from ... base import ProducerSpec
from ... schema import Triples

# In __init__:
self.register_specification(
    ProducerSpec(
        name = "explainability",
        schema = Triples,
    )
)
```

### 3. Генерация триплетов происхождения

**Файл:** `graphit-base/graphit/provenance/agent.py`

Создайте вспомогательные функции (подобные `question_triples`, `exploration_triples` и т.д. в GraphRAG):
```python
def agent_session_triples(session_uri, query, timestamp):
    """Generate triples for agent Question."""
    return [
        Triple(s=session_uri, p=RDF_TYPE, o=PROV_ACTIVITY),
        Triple(s=session_uri, p=RDF_TYPE, o=TG_QUESTION),
        Triple(s=session_uri, p=TG_QUERY, o=query),
        Triple(s=session_uri, p=PROV_STARTED_AT_TIME, o=timestamp),
    ]

def agent_iteration_triples(iteration_uri, parent_uri, thought, action, arguments, observation):
    """Generate triples for one Analysis step."""
    return [
        Triple(s=iteration_uri, p=RDF_TYPE, o=PROV_ENTITY),
        Triple(s=iteration_uri, p=RDF_TYPE, o=TG_ANALYSIS),
        Triple(s=iteration_uri, p=TG_THOUGHT, o=thought),
        Triple(s=iteration_uri, p=TG_ACTION, o=action),
        Triple(s=iteration_uri, p=TG_ARGUMENTS, o=json.dumps(arguments)),
        Triple(s=iteration_uri, p=TG_OBSERVATION, o=observation),
        Triple(s=iteration_uri, p=PROV_WAS_DERIVED_FROM, o=parent_uri),
    ]

def agent_final_triples(final_uri, parent_uri, answer):
    """Generate triples for Conclusion."""
    return [
        Triple(s=final_uri, p=RDF_TYPE, o=PROV_ENTITY),
        Triple(s=final_uri, p=RDF_TYPE, o=TG_CONCLUSION),
        Triple(s=final_uri, p=TG_ANSWER, o=answer),
        Triple(s=final_uri, p=PROV_WAS_DERIVED_FROM, o=parent_uri),
    ]
```

### 4. Определения типов

**Файл:** `graphit-base/graphit/provenance/namespaces.py`

Добавить типы сущностей, обеспечивающих объяснимость, и предикаты агентов:
```python
# Explainability entity types (used by both GraphRAG and Agent)
TG_QUESTION = TG + "Question"
TG_EXPLORATION = TG + "Exploration"
TG_FOCUS = TG + "Focus"
TG_SYNTHESIS = TG + "Synthesis"
TG_ANALYSIS = TG + "Analysis"
TG_CONCLUSION = TG + "Conclusion"

# Agent predicates
TG_THOUGHT = TG + "thought"
TG_ACTION = TG + "action"
TG_ARGUMENTS = TG + "arguments"
TG_OBSERVATION = TG + "observation"
TG_ANSWER = TG + "answer"
```

## Измененные файлы

| Файл | Изменение |
|------|--------|
| `graphit-base/graphit/schema/services/agent.py` | Добавлены session_id и collection в AgentRequest |
| `graphit-base/graphit/messaging/translators/agent.py` | Обновлен переводчик для новых полей |
| `graphit-base/graphit/provenance/namespaces.py` | Добавлены типы сущностей, предикаты агента и предикаты Document RAG |
| `graphit-base/graphit/provenance/triples.py` | Добавлены типы TG для конструкторов троек GraphRAG, добавлены конструкторы троек Document RAG |
| `graphit-base/graphit/provenance/uris.py` | Добавлены генераторы URI для Document RAG |
| `graphit-base/graphit/provenance/__init__.py` | Экспортированы новые типы, предикаты и функции Document RAG |
| `graphit-base/graphit/schema/services/retrieval.py` | Добавлены explain_id и explain_graph в DocumentRagResponse |
| `graphit-base/graphit/messaging/translators/retrieval.py` | Обновлен DocumentRagResponseTranslator для полей, связанных с объяснением |
| `graphit-flow/graphit/agent/react/service.py` | Добавлена логика создания и записи информации о объяснении |
| `graphit-flow/graphit/retrieval/document_rag/document_rag.py` | Добавлен колбэк для информации о объяснении и выводятся тройки, содержащие информацию о происхождении |
| `graphit-flow/graphit/retrieval/document_rag/rag.py` | Добавлен генератор информации о объяснении и подключен колбэк |
| `graphit-cli/graphit/cli/show_explain_trace.py` | Обработка типов трассировки агента |
| `graphit-cli/graphit/cli/list_explain_traces.py` | Отображение сессий агента вместе с GraphRAG |

## Созданные файлы

| Файл | Назначение |
|------|---------|
| `graphit-base/graphit/provenance/agent.py` | Генераторы троек, специфичные для агента |

## Обновления CLI

**Обнаружение:** И GraphRAG, и вопросы агента имеют тип `tg:Question`. Отличаются следующим:
1. Шаблон URI: `urn:graphit:agent:` против `urn:graphit:question:`
2. Выводимые сущности: `tg:Analysis` (агент) против `tg:Exploration` (GraphRAG)

**`list_explain_traces.py`:**
Отображает столбец "Тип" (Агент против GraphRAG)

**`show_explain_trace.py`:**
Автоматически определяет тип трассировки
Отображение информации об агенте: Вопрос → Шаги анализа → Вывод

## Обратная совместимость

`session_id` по умолчанию равно `""` - старые запросы работают, но не будут содержать информацию о происхождении
`collection` по умолчанию равно `"default"` - разумная альтернатива
CLI корректно обрабатывает оба типа трассировки

## Проверка

```bash
# Run an agent query
gr-invoke-agent -q "What is the capital of France?"

# List traces (should show agent sessions with Type column)
gr-list-explain-traces -U graphit -C default

# Show agent trace
gr-show-explain-trace "urn:graphit:agent:xxx"
```

## Будущие задачи (не входят в этот PR)

Зависимости DAG (когда анализ N использует результаты нескольких предыдущих анализов)
Связь с конкретными инструментами (KnowledgeQuery → его трассировка GraphRAG)
Потоковая передача метаданных (отправлять по мере выполнения, а не пакетами в конце)
