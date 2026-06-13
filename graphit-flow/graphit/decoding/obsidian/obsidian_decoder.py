
"""
Decoder for Obsidian-style markdown notes. Splits YAML frontmatter from
the note body, extracts explicit relations ([[wikilinks]], #tags,
frontmatter fields) directly as deterministic graph triples, and forwards
the (bracket-stripped) body text downstream to the chunker so the existing
kg-extract-* services can also mine implicit relations from the prose.
"""

import re
import logging
import urllib.parse

import yaml

from ... schema import Document, TextDocument, Metadata, Triples
from ... schema import Triple, Term, IRI, LITERAL
from ... base import FlowProcessor, ConsumerSpec, ProducerSpec, LibrarianSpec
from ... rdf import RDF_LABEL, GRAPHIT_ENTITIES
from ... provenance import set_graph, GRAPH_SOURCE

# Module logger
logger = logging.getLogger(__name__)

default_ident = "obsidian-decoder"

RDF_LABEL_VALUE = Term(type=IRI, iri=RDF_LABEL)

# Matches a leading "---\n...\n---\n" YAML frontmatter block
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

# Matches [[Target]], [[Target|Alias]], ![[Target]], [[Target#^block]]
WIKILINK_RE = re.compile(r"!?\[\[([^\]|#^]+?)(?:#\^?[^\]|]+)?(?:\|([^\]]+))?\]\]")

# Matches Obsidian-style #tags, but not markdown "# Heading" (no trailing
# space requirement after '#').
TAG_RE = re.compile(r"(?<![\w#])#([A-Za-z][\w/-]*)")


def _split_frontmatter(text):
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text

    body = text[m.end():]

    try:
        meta = yaml.safe_load(m.group(1)) or {}
        if not isinstance(meta, dict):
            meta = {}
    except yaml.YAMLError:
        logger.warning(
            "Failed to parse Obsidian frontmatter as YAML", exc_info=True,
        )
        meta = {}

    return meta, body


def _clean_body(text):
    """Strip wikilink/tag punctuation, keeping the readable name, so
    downstream LLM-based extractors read natural prose."""

    def _link_sub(m):
        return m.group(2) if m.group(2) else m.group(1)

    text = WIKILINK_RE.sub(_link_sub, text)
    text = TAG_RE.sub(lambda m: m.group(1), text)
    return text


class Processor(FlowProcessor):

    def __init__(self, **params):

        id = params.get("id", default_ident)

        super(Processor, self).__init__(
            **params | {
                "id": id,
            }
        )

        self.register_specification(
            ConsumerSpec(
                name = "input",
                schema = Document,
                handler = self.on_message,
            )
        )

        self.register_specification(
            ProducerSpec(
                name = "output",
                schema = TextDocument,
            )
        )

        self.register_specification(
            ProducerSpec(
                name = "triples",
                schema = Triples,
            )
        )

        self.register_specification(
            LibrarianSpec()
        )

        logger.info("Obsidian decoder initialized")

    def to_uri(self, text):
        part = text.strip().replace(" ", "-").lower().encode("utf-8")
        quoted = urllib.parse.quote(part)
        return GRAPHIT_ENTITIES + quoted

    def _entity(self, name):
        return Term(type=IRI, iri=str(self.to_uri(name)))

    def _label_triple(self, entity_term, label):
        return Triple(
            s=entity_term,
            p=RDF_LABEL_VALUE,
            o=Term(type=LITERAL, value=str(label)),
        )

    async def on_message(self, msg, consumer, flow):

        v = msg.value()

        logger.info(f"Decoding Obsidian note {v.metadata.id}...")

        title = None

        if v.document_id:
            doc_meta = await flow.librarian.fetch_document_metadata(
                document_id=v.document_id,
            )
            if doc_meta and doc_meta.kind and doc_meta.kind not in (
                "text/markdown", "text/x-markdown",
            ):
                logger.error(
                    f"Unsupported MIME type: {doc_meta.kind}. "
                    f"Obsidian decoder only handles markdown notes. "
                    f"Ignoring document {v.metadata.id}."
                )
                return

            title = doc_meta.title if doc_meta else None

            text = await flow.librarian.fetch_document_text(
                document_id=v.document_id,
            )
        else:
            text = v.data.decode("utf-8")

        frontmatter, body = _split_frontmatter(text)

        if not title:
            title = frontmatter.get("title")
        if not title:
            heading = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
            title = heading.group(1).strip() if heading else v.metadata.id

        note_term = self._entity(title)
        note_uri = note_term.iri

        triples = [self._label_triple(note_term, title)]

        # Explicit wikilinks -> deterministic graph edges
        seen_targets = set()
        for m in WIKILINK_RE.finditer(body):
            target = m.group(1).strip()
            if not target or target in seen_targets:
                continue
            seen_targets.add(target)

            target_term = self._entity(target)
            triples.append(Triple(
                s=note_term,
                p=self._entity("links to"),
                o=target_term,
            ))
            triples.append(self._label_triple(target_term, target))

        # #tags -> membership edges
        seen_tags = set()
        for m in TAG_RE.finditer(body):
            tag = m.group(1).strip()
            if not tag or tag in seen_tags:
                continue
            seen_tags.add(tag)

            tag_term = self._entity(tag)
            triples.append(Triple(
                s=note_term,
                p=self._entity("tagged with"),
                o=tag_term,
            ))
            triples.append(self._label_triple(tag_term, tag))

        # Frontmatter scalar/list fields -> attribute edges
        for key, value in frontmatter.items():
            if key == "title":
                continue
            values = value if isinstance(value, (list, tuple)) else [value]
            for item in values:
                if item is None or isinstance(item, (dict, list)):
                    continue
                triples.append(Triple(
                    s=note_term,
                    p=self._entity(str(key)),
                    o=Term(type=LITERAL, value=str(item)),
                ))

        await flow("triples").send(Triples(
            metadata=Metadata(
                id=note_uri,
                root=v.metadata.root,
                collection=v.metadata.collection,
            ),
            triples=set_graph(triples, GRAPH_SOURCE),
        ))

        # Forward the bracket-stripped body inline; notes are small enough
        # that there's no need to round-trip through the librarian again.
        await flow("output").send(TextDocument(
            metadata=Metadata(
                id=note_uri,
                root=v.metadata.root,
                collection=v.metadata.collection,
            ),
            text=_clean_body(body).encode("utf-8"),
        ))

        logger.debug("Obsidian decoding complete")

    @staticmethod
    def add_args(parser):
        FlowProcessor.add_args(parser)


def run():

    Processor.launch(default_ident, __doc__)
