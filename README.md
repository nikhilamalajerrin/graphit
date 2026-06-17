<div align="center">

<img src="graphit-logo.svg" width="100%" alt="GraphIt" />

# GraphIt

The semantic deployment platform for context graphs, retrieval, agents, and explainable AI workflows.

</div>

GraphIt is infrastructure for building agent systems around structured, queryable context. It combines document ingestion, entity and relationship extraction, graph storage, vector retrieval, LLM orchestration, provenance, and observability into a composable processing platform.

The project is designed for private deployments where teams need their agents grounded in domain knowledge they can inspect, version, test, and operate.

## What GraphIt Provides

- Context graph construction from documents, data, ontologies, and extracted facts
- DocumentRAG, GraphRAG, and ontology-guided retrieval workflows
- Agent orchestration with ReAct, plan-then-execute, supervisor patterns, and MCP tools
- Multi-model storage for documents, graph triples, rows, and embeddings
- Pluggable LLM providers including OpenAI, Claude, Mistral, Cohere, Azure, Bedrock, Ollama, vLLM, TGI, LM Studio, and Snowflake Cortex
- Vector storage through Qdrant, Pinecone, and Milvus integrations
- Graph/triples backends including Cassandra, Neo4j, Memgraph, FalkorDB, and Snowflake
- File/object storage and streaming infrastructure integrations
- API gateway, CLI tools, Python clients, and TypeScript UI client packages
- Prometheus, Grafana, and Loki observability support

## Repository Layout

```text
graphit-base/             Core schemas, clients, service base classes, config helpers
graphit-flow/             Flow processors, query/storage backends, LLM providers, gateway
graphit-cli/              Command-line tools
graphit-embeddings-hf/    Hugging Face embedding provider
graphit-bedrock/          AWS Bedrock text completion provider
graphit-vertexai/         Google Vertex AI / AI Studio providers
graphit-mcp/              MCP server integration
graphit-ocr/              OCR decoder package
graphit-unstructured/     Universal document decoder package
docs/                     Technical documentation
specs/                    API and websocket specs
tests/                    Unit, contract, and integration tests
dev-tools/                Development utilities and local processor group configs
```

## Quickstart

GraphIt is usually run as a set of containers generated from a deployment configuration. The configuration tool produces a `deploy.zip` containing either a Docker/Podman Compose file or Kubernetes resources plus installation instructions.

```bash
npx @graphit/config
```

For source development, use a Python virtual environment and install the local packages you need:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e graphit-base -e graphit-flow -e graphit-cli
```

Install optional provider packages as needed, for example:

```bash
pip install -e graphit-embeddings-hf
pip install -e graphit-bedrock
pip install -e graphit-vertexai
```

## Local Development

The development processor group lets you run many processors in one local Python process while using external infrastructure services such as Cassandra, Qdrant, RabbitMQ, Garage, Prometheus, Grafana, and Loki.

See:

```text
dev-tools/proc-group/README.md
```

The main application UI is expected on:

```text
http://localhost:8888
```

Grafana telemetry is expected on:

```text
http://localhost:3000
```

## Snowflake Support

GraphIt includes Snowflake-oriented components for enterprise graph workflows:

- `graphit.base.snowflake_config` for shared Snowflake connection parameters
- `triples-write-snowflake` for writing graph triples into Snowflake
- `triples-query-snowflake` for querying graph triples from Snowflake
- `text-completion-cortex` for Snowflake Cortex text completion
- `obsidian-decoder` and `gr-load-obsidian-vault` for loading Obsidian-style knowledge vaults

Common Snowflake environment variables:

```bash
export SNOWFLAKE_ACCOUNT=...
export SNOWFLAKE_USER=...
export SNOWFLAKE_PASSWORD=...
export SNOWFLAKE_WAREHOUSE=...
export SNOWFLAKE_DATABASE=...
export SNOWFLAKE_ROLE=...
```

## Testing

The test suite is organized into unit, contract, and integration tests:

```text
tests/unit/
tests/contract/
tests/integration/
```

Install test dependencies:

```bash
cd tests
pip install -r requirements.txt
cd ..
```

Run the full test suite:

```bash
pytest
```

Run tests with verbose output:

```bash
pytest -v
```

Run a specific test file:

```bash
pytest tests/unit/test_text_completion/test_vertexai_processor.py
```

Run a specific test class or method:

```bash
pytest tests/unit/test_text_completion/test_vertexai_processor.py::TestVertexAIProcessorInitialization
pytest tests/unit/test_text_completion/test_vertexai_processor.py::TestVertexAIProcessorInitialization::test_processor_initialization_with_valid_credentials
```

Run by marker:

```bash
pytest -m unit
pytest -m integration
pytest -m "not slow"
```

Run with coverage:

```bash
pytest --cov=graphit
pytest --cov=graphit --cov-report=html
pytest --cov=graphit --cov-report=term-missing
pytest --cov=graphit --cov-fail-under=80
```

Useful focused checks for the Snowflake/Obsidian work:

```bash
pytest tests/unit/test_knowledge_graph/test_obsidian_decoder.py -v
python -m compileall graphit-base graphit-flow graphit-cli
```

Additional testing references:

- [TESTS.md](TESTS.md)
- [TEST_SETUP.md](TEST_SETUP.md)
- [TEST_STRATEGY.md](TEST_STRATEGY.md)
- [TEST_CASES.md](TEST_CASES.md)

## Observability

When the platform is running, Grafana is available at:

```text
http://localhost:3000
```

Default local credentials:

```text
user: admin
password: admin
```

The default observability stack tracks latency, errors, request rates, queue backlogs, chunking histograms, service CPU/memory usage, token throughput, and model/cost metrics.

## License

GraphIt is licensed under the Apache License 2.0. See [LICENSE](LICENSE).
