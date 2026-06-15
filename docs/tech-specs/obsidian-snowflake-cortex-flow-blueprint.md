---
layout: default
title: "Example: Obsidian Vault -> Snowflake Graph -> Cortex Reasoning"
parent: "Tech Specs"
---

# Example Flow Blueprint: Obsidian Vault → Snowflake Graph → Cortex Reasoning

This is a worked example of a flow blueprint (see
[Flow Blueprint Definition Specification](flow-blueprint-definition.md) for
the general format) that wires together:

- `obsidian-decoder` — parses Obsidian markdown notes (frontmatter,
  `[[wikilinks]]`, `#tags`) into deterministic graph triples, and forwards
  the note body to the existing chunker for implicit/LLM-based extraction.
- `chunker` / `kg-extract-relationships` / `kg-extract-definitions` —
  unmodified, existing GraphIt processors.
- `triples-write-snowflake` / `triples-query-snowflake` — the Snowflake
  triples store backend.
- `text-completion-cortex` — Snowflake Cortex as the reasoning LLM, shared
  by GraphRAG and the agent-orchestrator.

This is **not pushed automatically**. Save this as `obsidian.json` and push
it with the existing CLI:

```bash
gr-put-flow-blueprint --id obsidian --file obsidian.json
```

Then load a vault with:

```bash
gr-load-obsidian-vault --flow-id obsidian /path/to/vault
```

```json
{
  "description": "Obsidian vault ingestion with Snowflake graph storage and Cortex reasoning",
  "tags": ["obsidian", "snowflake", "cortex"],

  "class": {
    "text-completion:{class}": {
      "request": "non-persistent://tg/request/text-completion:{class}",
      "response": "non-persistent://tg/response/text-completion:{class}",
      "settings": {
        "model": "{model}"
      }
    },
    "triples-query-snowflake:{class}": {
      "request": "non-persistent://tg/request/triples-query:{class}",
      "response": "non-persistent://tg/response/triples-query:{class}"
    }
  },

  "flow": {
    "obsidian-decoder:{id}": {
      "input": "persistent://tg/flow/{workspace}:document-load:{id}",
      "output": "persistent://tg/flow/{workspace}:chunk-load:{id}",
      "triples": "persistent://tg/flow/{workspace}:triples-store:{id}"
    },
    "chunker:{id}": {
      "input": "persistent://tg/flow/{workspace}:chunk-load:{id}",
      "output": "persistent://tg/flow/{workspace}:chunk:{id}",
      "settings": {
        "chunk_size": "{chunk}",
        "chunk_overlap": 100
      }
    },
    "kg-extract-relationships:{id}": {
      "input": "persistent://tg/flow/{workspace}:chunk:{id}",
      "triples": "persistent://tg/flow/{workspace}:triples-store:{id}"
    },
    "kg-extract-definitions:{id}": {
      "input": "persistent://tg/flow/{workspace}:chunk:{id}",
      "triples": "persistent://tg/flow/{workspace}:triples-store:{id}"
    },
    "triples-write-snowflake:{id}": {
      "input": "persistent://tg/flow/{workspace}:triples-store:{id}"
    }
  },

  "interfaces": {
    "document-load": "persistent://tg/flow/{workspace}:document-load:{id}",
    "triples-store": "persistent://tg/flow/{workspace}:triples-store:{id}",
    "triples-query": {
      "request": "non-persistent://tg/request/triples-query:{class}",
      "response": "non-persistent://tg/response/triples-query:{class}"
    },
    "text-completion": {
      "request": "non-persistent://tg/request/text-completion:{class}",
      "response": "non-persistent://tg/response/text-completion:{class}"
    }
  },

  "parameters": {
    "model": "llm-model",
    "chunk": "chunk-size"
  }
}
```

Deploy `obsidian-decoder`, `triples-write-snowflake`, `triples-query-snowflake`
and `text-completion-cortex` with the matching `--snowflake-*` flags (or
`SNOWFLAKE_ACCOUNT` / `SNOWFLAKE_USER` / `SNOWFLAKE_PASSWORD` /
`SNOWFLAKE_WAREHOUSE` / `SNOWFLAKE_DATABASE` / `SNOWFLAKE_ROLE` environment
variables) so all three connect to the same Snowflake account/database.
Confirm the Cortex model name passed via `{model}` (e.g. `mistral-large2`,
`llama3.1-70b`) is enabled on your account/region before launching the flow.
