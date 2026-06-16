"""
Unit tests for the Obsidian decoder.

Covers frontmatter/body splitting, wikilink and tag extraction, body
cleanup, and the end-to-end on_message triple/TextDocument emission.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from graphit.decoding.obsidian.obsidian_decoder import (
    Processor, _split_frontmatter, _clean_body, WIKILINK_RE, TAG_RE,
)
from graphit.schema import Document, Metadata, Triples, TextDocument, IRI, LITERAL
from graphit.rdf import GRAPHIT_ENTITIES, RDF_LABEL


NOTE = """---
title: Marie Curie
tags: [scientist, nobel]
---
# Marie Curie

Marie Curie worked with [[Pierre Curie]] on [[Radioactivity]] research.
She is tagged #physics and #chemistry.
See also [[Nobel Prize|the prize]] and ![[embedded-note]] and [[Block Ref#^xyz]].
"""


@pytest.fixture
def processor():
    return Processor(taskgroup=AsyncMock(), id="test-obsidian-decoder")


def _make_document_message(text=NOTE, doc_id="note-1", collection="default"):
    metadata = Metadata(id=doc_id, root=doc_id, collection=collection)
    value = Document(metadata=metadata, data=text.encode("utf-8"))
    msg = MagicMock()
    msg.value.return_value = value
    return msg


class TestSplitFrontmatter:

    def test_parses_yaml_and_strips_block(self):
        meta, body = _split_frontmatter(NOTE)

        assert meta == {"title": "Marie Curie", "tags": ["scientist", "nobel"]}
        assert "---" not in body
        assert body.startswith("# Marie Curie")

    def test_no_frontmatter_returns_empty_meta(self):
        text = "# Just a note\n\nNo frontmatter here."
        meta, body = _split_frontmatter(text)

        assert meta == {}
        assert body == text

    def test_invalid_yaml_falls_back_to_empty_meta(self):
        text = "---\n: not valid yaml: [\n---\nBody text\n"
        meta, body = _split_frontmatter(text)

        assert meta == {}
        assert body == "Body text\n"


class TestWikilinkAndTagExtraction:

    def test_wikilink_variants(self):
        body = "[[Plain]] [[Target|Alias]] ![[Embed]] [[WithBlock#^abc]]"
        matches = WIKILINK_RE.findall(body)

        targets = [m[0] for m in matches]
        assert "Plain" in targets
        assert "Target" in targets
        assert "Embed" in targets
        assert "WithBlock" in targets

        alias_map = {m[0]: m[1] for m in matches}
        assert alias_map["Target"] == "Alias"

    def test_tags_match_but_headings_do_not(self):
        body = "# Heading\nSome #tag1 and #tag2/nested text."
        tags = TAG_RE.findall(body)

        assert tags == ["tag1", "tag2/nested"]

    def test_clean_body_strips_punctuation_keeps_names(self):
        body = "See [[Target|Alias]] and ![[Embed]] and #tag."
        cleaned = _clean_body(body)

        assert cleaned == "See Alias and Embed and tag."


class TestProcessorEntityUri:

    def test_to_uri_matches_relationships_extractor_convention(self):
        p = Processor.__new__(Processor)
        uri = p.to_uri("Marie Curie")

        assert uri == GRAPHIT_ENTITIES + "marie-curie"


@pytest.mark.asyncio
class TestObsidianDecoderOnMessage:

    async def test_emits_explicit_triples_and_cleaned_body(self, processor):
        msg = _make_document_message()

        triples_sent = AsyncMock()
        output_sent = AsyncMock()

        def flow(name):
            if name == "triples":
                return MagicMock(send=triples_sent)
            elif name == "output":
                return MagicMock(send=output_sent)
            return MagicMock()

        await processor.on_message(msg, MagicMock(), flow)

        # Triples message was sent
        triples_sent.assert_awaited_once()
        triples_msg = triples_sent.call_args[0][0]
        assert isinstance(triples_msg, Triples)

        def labels_for(iri):
            return {
                t.o.value for t in triples_msg.triples
                if t.s.iri == iri and t.p.iri == RDF_LABEL
            }

        note_uri = GRAPHIT_ENTITIES + "marie-curie"
        pierre_uri = GRAPHIT_ENTITIES + "pierre-curie"
        radioactivity_uri = GRAPHIT_ENTITIES + "radioactivity"
        links_to_uri = GRAPHIT_ENTITIES + "links-to"
        tagged_with_uri = GRAPHIT_ENTITIES + "tagged-with"
        physics_uri = GRAPHIT_ENTITIES + "physics"

        # Note got its own label
        assert labels_for(note_uri) == {"Marie Curie"}

        # Wikilinks became links-to edges, with labels on the targets
        link_edges = {
            (t.s.iri, t.o.iri) for t in triples_msg.triples
            if t.p.iri == links_to_uri
        }
        assert (note_uri, pierre_uri) in link_edges
        assert (note_uri, radioactivity_uri) in link_edges
        assert labels_for(pierre_uri) == {"Pierre Curie"}

        # Tags became tagged-with edges
        tag_edges = {
            (t.s.iri, t.o.iri) for t in triples_msg.triples
            if t.p.iri == tagged_with_uri
        }
        assert (note_uri, physics_uri) in tag_edges

        # Frontmatter list field became attribute triples
        tags_attr_uri = GRAPHIT_ENTITIES + "tags"
        attr_values = {
            t.o.value for t in triples_msg.triples
            if t.s.iri == note_uri and t.p.iri == tags_attr_uri
        }
        assert attr_values == {"scientist", "nobel"}

        # Cleaned body forwarded downstream, brackets stripped
        output_sent.assert_awaited_once()
        text_doc = output_sent.call_args[0][0]
        assert isinstance(text_doc, TextDocument)
        body_text = text_doc.text.decode("utf-8")
        assert "[[" not in body_text
        assert "Pierre Curie" in body_text
        assert "the prize" in body_text
