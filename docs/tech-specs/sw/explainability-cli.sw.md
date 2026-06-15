---
layout: default
title: "Maelezo ya Kiufundi ya Zana za Amri (CLI) za Ufafanuzi"
parent: "Swahili (Beta)"
---

# Maelezo ya Kiufundi ya Zana za Amri (CLI) za Ufafanuzi

> **Beta Translation:** This document was translated via Machine Learning and as such may not be 100% accurate. All non-English languages are currently classified as Beta.

## Hali

Rasimu

## Muhtasari

Maelezo haya yanaeleza zana za amri (CLI) za kuchanganua na kuchunguza data ya ufafanuzi katika GraphIt. Zana hizi zinawawezesha watumiaji kufuatilia jinsi majibu yalivyopatikana na kuchanganua mnyororo wa asili kutoka kwa uhusiano (edges) hadi kwenye nyaraka za asili.

Zana tatu za CLI:

1. **`gr-show-document-hierarchy`** - Onyesha hierarkia ya nyaraka → kurasa → vipande → uhusiano
2. **`gr-list-explain-traces`** - Orodha ya vipindi vyote vya GraphRAG na maswali
3. **`gr-show-explain-trace`** - Onyesha mnyororo kamili wa ufafanuzi kwa kipindi

## Lengo

**Uchanganuzi**: Kuwawezesha watengenezaji kuchunguza matokeo ya usindikaji wa nyaraka
**Ufuatiliaji**: Kufuatilia ukweli wowote uliopatikana hadi kwenye nyaraka yake ya asili
**Unyonyaji**: Kuonyesha jinsi GraphRAG ilivyopata jibu
**Urahisi wa Matumizi**: Kiolesura rahisi cha CLI na mipangilio ya kawaida

## Asili

GraphIt ina mifumo miwili ya asili:

1. **Asili ya wakati wa uundaji** (angalia `extraction-time-provenance.md`): Inarecord uhusiano wa nyaraka → kurasa → vipande → uhusiano wakati wa kuingizwa. Hifadhiwa katika grafu iliyoitwa `urn:graph:source` kwa kutumia `prov:wasDerivedFrom`.

2. **Ufafanuzi wa wakati wa kuulizia** (angalia `query-time-explainability.md`): Inarecord mnyororo wa swali → uchunguzi → umakini → muhtasari wakati wa maswali ya GraphRAG. Hifadhiwa katika grafu iliyoitwa `urn:graph:retrieval`.

Mapungufu ya sasa:
Hakuna njia rahisi ya kuonyesha hierarkia ya nyaraka baada ya usindikaji
Lazima kuulize data ya ufafanuzi kwa kutumia triples
Hakuna mtazamo uliochanganywa wa kipindi cha GraphRAG

## Muundo wa Kiufundi

### Zana 1: gr-show-document-hierarchy

**Lengo**: Ikiwa unapokea kitambulisho cha nyaraka, tembea na uonyeshe vitu vyote vilivyotokana.

**Matumizi**:
```bash
gr-show-document-hierarchy "urn:graphit:doc:abc123"
gr-show-document-hierarchy --show-content --max-content 500 "urn:graphit:doc:abc123"
```

**Vigezo**:
| Arg | Maelezo |
|-----|-------------|
| `document_id` | URI ya hati (ya nafasi) |
| `-u/--api-url` | URL ya lango (ya kawaida: `$GRAPHIT_URL`) |
| `-t/--token` | Ishara ya uthibitishaji (ya kawaida: `$GRAPHIT_TOKEN`) |
| `-U/--user` | Kitambulisho cha mtumiaji (ya kawaida: `graphit`) |
| `-C/--collection` | Mkusanyiko (ya kawaida: `default`) |
| `--show-content` | Jumuisha yaliyomo katika faili/hati |
| `--max-content` | Herufi nyingi kwa kila faili (ya kawaida: 200) |
| `--format` | Matokeo: `tree` (ya kawaida), `json` |

**Utendaji**:
1. Tafuta data: `?child prov:wasDerivedFrom <document_id>` katika `urn:graph:source`
2. Tafuta kwa urudi-urudi watoto wa kila matokeo
3. Jenga muundo wa mti: Hati → Kurasa → Sehemu
4. Ikiwa `--show-content`, pata yaliyomo kutoka kwa API ya msimamizi
5. Onyesha kama mti ulioainishwa au JSON

**Mfano wa Matokeo**:
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

### Zana 2: gr-list-explain-traces

**Madhumuni**: Kuorodhesha vipindi vyote vya GraphRAG (maswali) katika mkusanyiko.

**Matumizi**:
```bash
gr-list-explain-traces
gr-list-explain-traces --limit 20 --format json
```

**Vigezo**:
| Arg | Maelezo |
|-----|-------------|
| `-u/--api-url` | URL ya lango |
| `-t/--token` | Token ya uthibitishaji |
| `-U/--user` | Kitambulisho cha mtumiaji |
| `-C/--collection` | Mkusanyiko |
| `--limit` | Matokeo ya juu (ya kawaida: 50) |
| `--format` | Matokeo: `table` (ya kawaida), `json` |

**Utekelezaji**:
1. Uliza: `?session tg:query ?text` katika `urn:graph:retrieval`
2. Uliza alama za wakati: `?session prov:startedAtTime ?time`
3. Onyesha kama jedwali

**Mfano wa Matokeo**:
```
Session ID                                    | Question                        | Time
----------------------------------------------|--------------------------------|---------------------
urn:graphit:question:abc123                | What was the War on Terror?    | 2024-01-15 10:30:00
urn:graphit:question:def456                | Who founded OpenAI?            | 2024-01-15 09:15:00
```

### Zana 3: gr-show-explain-trace

**Madhumuni**: Kuonyesha mnyororo kamili wa uelewaji kwa kipindi cha GraphRAG.

**Matumizi**:
```bash
gr-show-explain-trace "urn:graphit:question:abc123"
gr-show-explain-trace --max-answer 1000 --show-provenance "urn:graphit:question:abc123"
```

**Vigezo**:
| Arg | Maelezo |
|-----|-------------|
| `question_id` | URI ya swali (nafasi) |
| `-u/--api-url` | URL ya lango |
| `-t/--token` | Ishara ya uthibitishaji |
| `-U/--user` | Kitambulisho cha mtumiaji |
| `-C/--collection` | Mkusanyiko |
| `--max-answer` | Idadi ya juu ya herufi kwa jibu (ya kawaida: 500) |
| `--show-provenance` | Fuatilia miunganisho hadi kwenye hati za asili |
| `--format` | Pato: `text` (ya kawaida), `json` |

**Utendaji**:
1. Pata maandishi ya swali kutoka kwa `tg:query`.
2. Tafuta utafutaji: `?exp prov:wasGeneratedBy <question_id>`
3. Tafuta umakini: `?focus prov:wasDerivedFrom <exploration_id>`
4. Pata miunganisho iliyochaguliwa: `<focus_id> tg:selectedEdge ?edge`
5. Kwa kila muunganisho, pata `tg:edge` (triple iliyotiwa mabano) na `tg:reasoning`.
6. Tafuta muhtasari: `?synth prov:wasDerivedFrom <focus_id>`
7. Pata jibu kutoka kwa `tg:document` kupitia msimamizi wa maktaba.
8. Ikiwa `--show-provenance`, fuatilia miunganisho hadi kwenye hati za asili.

**Mfano wa Pato**:
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

## Faili Zinazotakazwa Kuundwa

| Faili | Madhumuni |
|------|---------|
| `graphit-cli/graphit/cli/show_document_hierarchy.py` | Chombo 1 |
| `graphit-cli/graphit/cli/list_explain_traces.py` | Chombo 2 |
| `graphit-cli/graphit/cli/show_explain_trace.py` | Chombo 3 |

## Faili Zinazotakazwa Kurekebishwa

| Faili | Marekebisho |
|------|--------|
| `graphit-cli/setup.py` | Ongeza vipengele vya `console_scripts` |

## Maelezo ya Utendaji

1. **Usalama wa yaliyomo ya binary**: Jaribu kusimbua kwa UTF-8; ikiwa hufanikiwa, onyesha `[Binary: {size} bytes]`
2. **Ufupishaji**: Zifuata sheria za `--max-content`/`--max-answer` pamoja na ishara ya `[truncated]`
3. **Manuku matatu yaliyotiwa:** Changanua muundo wa RDF-star kutoka kwa `predicate` ya `tg:edge`
4. **Mifumo:** Fuata mifumo iliyopo ya CLI kutoka `query_graph.py`

## Masuala ya Usalama

Maswali yote yanazingatia mipaka ya mtumiaji/mkusanyiko
Uthibitishaji wa token unaoendeshwa kupitia `--token` au `$GRAPHIT_TOKEN`

## Mkakati wa Upimaji

Uthibitisho wa mwongozo kwa data ya mfano:
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

## Marejeleo

Uwezekano wa kueleza matokeo wakati wa swali: `docs/tech-specs/query-time-explainability.md`
Chanzo cha data wakati wa uundaji: `docs/tech-specs/extraction-time-provenance.md`
Kifaa cha amri (CLI) cha mfano uliopo: `graphit-cli/graphit/cli/invoke_graph_rag.py`
