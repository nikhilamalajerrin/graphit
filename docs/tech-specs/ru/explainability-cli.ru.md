---
layout: default
title: "Техническая спецификация CLI для Explainability"
parent: "Russian (Beta)"
---

# Техническая спецификация CLI для Explainability

> **Beta Translation:** This document was translated via Machine Learning and as such may not be 100% accurate. All non-English languages are currently classified as Beta.

## Статус

Черновик

## Обзор

Эта спецификация описывает инструменты командной строки для отладки и изучения данных explainability в GraphIt. Эти инструменты позволяют пользователям отслеживать, как были получены ответы, и отлаживать цепочку происхождения от ребер до исходных документов.

Три инструмента командной строки:

1. **`gr-show-document-hierarchy`** - Отображение иерархии документ → страница → фрагмент → ребро
2. **`gr-list-explain-traces`** - Список всех сессий GraphRAG с вопросами
3. **`gr-show-explain-trace`** - Отображение полной цепочки explainability для сессии

## Цели

**Отладка**: Предоставить разработчикам возможность просматривать результаты обработки документов.
**Прослеживаемость**: Отслеживать любой извлеченный факт до его исходного документа.
**Прозрачность**: Показать, как GraphRAG получил ответ.
**Удобство использования**: Простой интерфейс командной строки с разумными значениями по умолчанию.

## Предыстория

GraphIt имеет две системы отслеживания происхождения:

1. **Отслеживание происхождения во время извлечения** (см. `extraction-time-provenance.md`): Записывает отношения документ → страница → фрагмент → ребро во время импорта. Хранится в графе с именем `urn:graph:source`, используя `prov:wasDerivedFrom`.

2. **Explainability во время запроса** (см. `query-time-explainability.md`): Записывает цепочку вопрос → исследование → фокус → синтез во время запросов GraphRAG. Хранится в графе с именем `urn:graph:retrieval`.

Текущие ограничения:
Нет простого способа визуализации иерархии документов после обработки.
Необходимо вручную запрашивать тройки для просмотра данных explainability.
Нет единого представления сессии GraphRAG.

## Технический дизайн

### Инструмент 1: gr-show-document-hierarchy

**Назначение**: При заданном идентификаторе документа, обходит и отображает все производные сущности.

**Использование**:
```bash
gr-show-document-hierarchy "urn:graphit:doc:abc123"
gr-show-document-hierarchy --show-content --max-content 500 "urn:graphit:doc:abc123"
```

**Аргументы**:
| Аргумент | Описание |
|-----|-------------|
| `document_id` | URI документа (позиционный) |
| `-u/--api-url` | URL шлюза (по умолчанию: `$GRAPHIT_URL`) |
| `-t/--token` | Токен авторизации (по умолчанию: `$GRAPHIT_TOKEN`) |
| `-U/--user` | Идентификатор пользователя (по умолчанию: `graphit`) |
| `-C/--collection` | Коллекция (по умолчанию: `default`) |
| `--show-content` | Включить содержимое блоба/документа |
| `--max-content` | Максимальное количество символов на блоб (по умолчанию: 200) |
| `--format` | Вывод: `tree` (по умолчанию), `json` |

**Реализация**:
1. Запрос троек: `?child prov:wasDerivedFrom <document_id>` в `urn:graph:source`
2. Рекурсивный запрос дочерних элементов каждого результата
3. Построение древовидной структуры: Документ → Страницы → Части
4. Если `--show-content`, получение содержимого из API librarian
5. Отображение в виде отформатированного дерева или JSON

**Пример вывода**:
```
Document: urn:graphit:doc:abc123
  Title: "Sample PDF"
  Type: application/pdf

  └── Page 1: urn:graphit:doc:abc123/p1
      ├── Chunk 0: urn:graphit:doc:abc123/p1/c0
      │   Content: "The quick brown fox..." [truncated]
      └── Chunk 1: urn:graphit:doc:abc123/p1/c1
          Content: "Machine learning is..." [truncated]
```

### Инструмент 2: gr-list-explain-traces

**Назначение**: Вывести список всех сессий GraphRAG (вопросов) в коллекции.

**Использование**:
```bash
gr-list-explain-traces
gr-list-explain-traces --limit 20 --format json
```

**Аргументы**:
| Аргумент | Описание |
|-----|-------------|
| `-u/--api-url` | URL шлюза |
| `-t/--token` | Токен авторизации |
| `-U/--user` | Идентификатор пользователя |
| `-C/--collection` | Коллекция |
| `--limit` | Максимальное количество результатов (по умолчанию: 50) |
| `--format` | Вывод: `table` (по умолчанию), `json` |

**Реализация**:
1. Запрос: `?session tg:query ?text` в `urn:graph:retrieval`
2. Запрос временных меток: `?session prov:startedAtTime ?time`
3. Отображение в виде таблицы

**Пример вывода**:
```
Session ID                                    | Question                        | Time
----------------------------------------------|--------------------------------|---------------------
urn:graphit:question:abc123                | What was the War on Terror?    | 2024-01-15 10:30:00
urn:graphit:question:def456                | Who founded OpenAI?            | 2024-01-15 09:15:00
```

### Инструмент 3: gr-show-explain-trace

**Назначение**: Отображение полной цепочки объяснений для сеанса GraphRAG.

**Использование**:
```bash
gr-show-explain-trace "urn:graphit:question:abc123"
gr-show-explain-trace --max-answer 1000 --show-provenance "urn:graphit:question:abc123"
```

**Аргументы**:
| Аргумент | Описание |
|-----|-------------|
| `question_id` | URI вопроса (позиционный) |
| `-u/--api-url` | URL шлюза |
| `-t/--token` | Токен авторизации |
| `-U/--user` | Идентификатор пользователя |
| `-C/--collection` | Коллекция |
| `--max-answer` | Максимальное количество символов для ответа (по умолчанию: 500) |
| `--show-provenance` | Проследить связи к исходным документам |
| `--format` | Вывод: `text` (по умолчанию), `json` |

**Реализация**:
1. Получить текст вопроса из предиката `tg:query`
2. Найти исследование: `?exp prov:wasGeneratedBy <question_id>`
3. Найти фокус: `?focus prov:wasDerivedFrom <exploration_id>`
4. Получить выбранные связи: `<focus_id> tg:selectedEdge ?edge`
5. Для каждой связи, получить `tg:edge` (цитируемая тройка) и `tg:reasoning`
6. Найти синтез: `?synth prov:wasDerivedFrom <focus_id>`
7. Получить ответ из `tg:document` через библиотекаря
8. Если `--show-provenance`, проследить связи к исходным документам

**Пример вывода**:
```
=== GraphRAG Session: urn:graphit:question:abc123 ===

Question: What was the War on Terror?
Time: 2024-01-15 10:30:00

--- Exploration ---
Retrieved 50 edges from knowledge graph

--- Focus (Edge Selection) ---
Selected 12 edges:

  1. (War on Terror, definition, "A military campaign...")
     Reasoning: Directly defines the subject of the query
     Source: chunk → page 2 → "Beyond the Vigilant State"

  2. (Guantanamo Bay, part_of, War on Terror)
     Reasoning: Shows key component of the campaign

--- Synthesis ---
Answer:
  The War on Terror was a military campaign initiated...
  [truncated at 500 chars]
```

## Файлы для создания

| Файл | Назначение |
|------|---------|
| `graphit-cli/graphit/cli/show_document_hierarchy.py` | Инструмент 1 |
| `graphit-cli/graphit/cli/list_explain_traces.py` | Инструмент 2 |
| `graphit-cli/graphit/cli/show_explain_trace.py` | Инструмент 3 |

## Файлы для изменения

| Файл | Изменение |
|------|--------|
| `graphit-cli/setup.py` | Добавить записи в console_scripts |

## Замечания по реализации

1. **Безопасность двоичного содержимого**: Попробуйте декодировать в UTF-8; если не удается, отобразите `[Binary: {size} bytes]`.
2. **Усечение**: Соблюдайте `--max-content`/`--max-answer` с индикатором `[truncated]`.
3. **Тройки в кавычках**: Разберите формат RDF-star из предиката `tg:edge`.
4. **Шаблоны**: Следуйте существующим шаблонам CLI из `query_graph.py`.

## Вопросы безопасности

Все запросы соответствуют границам пользователя/коллекции.
Поддерживается аутентификация по токену через `--token` или `$GRAPHIT_TOKEN`.

## Стратегия тестирования

Ручная проверка с использованием образцовых данных:
```bash
# Load a test document
gr-load-pdf -f test.pdf -c test-collection

# Verify hierarchy
gr-show-document-hierarchy "urn:graphit:doc:test"

# Run a GraphRAG query with explainability
gr-invoke-graph-rag --explainable -q "Test question"

# List and inspect traces
gr-list-explain-traces
gr-show-explain-trace "urn:graphit:question:xxx"
```

## Ссылки

Объяснимость во время выполнения запроса: `docs/tech-specs/query-time-explainability.md`
Происхождение во время извлечения: `docs/tech-specs/extraction-time-provenance.md`
Существующий пример интерфейса командной строки: `graphit-cli/graphit/cli/invoke_graph_rag.py`
