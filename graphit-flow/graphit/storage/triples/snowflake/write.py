
"""
Graph writer.  Input is graph edge.  Writes edges to a Snowflake table.
"""

import re
import asyncio
import logging

from .... base import TriplesStoreService, CollectionConfigHandler
from .... base.snowflake_config import add_snowflake_args, resolve_snowflake_config
from .... schema import IRI, LITERAL, BLANK, TRIPLE

# Module logger
logger = logging.getLogger(__name__)

default_ident = "triples-write"

DEFAULT_GRAPH = ""

TABLE_NAME = "TRIPLES"


def _safe_ident(name):
    """Sanitize a workspace/collection name into a safe Snowflake schema
    identifier."""
    safe = re.sub(r"[^A-Za-z0-9_]", "_", name or "") or "DEFAULT"
    return safe.upper()


def serialize_triple(triple):
    """Serialize a Triple object to JSON for storage."""
    import json

    if triple is None:
        return None

    def term_to_dict(term):
        if term is None:
            return None

        result = {"type": term.type}
        if term.type == IRI:
            result["iri"] = term.iri
        elif term.type == LITERAL:
            result["value"] = term.value
            if term.datatype:
                result["datatype"] = term.datatype
            if term.language:
                result["language"] = term.language
        elif term.type == BLANK:
            result["id"] = term.id
        elif term.type == TRIPLE:
            result["triple"] = serialize_triple(term.triple)
        return result

    return json.dumps({
        "s": term_to_dict(triple.s),
        "p": term_to_dict(triple.p),
        "o": term_to_dict(triple.o),
    })


def get_term_value(term):
    """Extract the string value from a Term"""
    if term is None:
        return None
    if term.type == IRI:
        return term.iri
    elif term.type == LITERAL:
        return term.value
    elif term.type == TRIPLE:
        return serialize_triple(term.triple)
    else:
        return term.id or term.value


def get_term_otype(term):
    if term is None:
        return "u"
    if term.type == IRI or term.type == BLANK:
        return "u"
    elif term.type == LITERAL:
        return "l"
    elif term.type == TRIPLE:
        return "t"
    else:
        return "u"


def get_term_dtype(term):
    if term is None:
        return ""
    if term.type == LITERAL:
        return term.datatype or ""
    return ""


def get_term_lang(term):
    if term is None:
        return ""
    if term.type == LITERAL:
        return term.language or ""
    return ""


class Processor(CollectionConfigHandler, TriplesStoreService):

    def __init__(self, **params):

        id = params.get("id", default_ident)

        self.snowflake_config = resolve_snowflake_config(
            account=params.get("snowflake_account"),
            user=params.get("snowflake_user"),
            password=params.get("snowflake_password"),
            warehouse=params.get("snowflake_warehouse"),
            database=params.get("snowflake_database"),
            role=params.get("snowflake_role"),
        )

        super(Processor, self).__init__(
            **params | {
                "snowflake_account": self.snowflake_config["account"],
                "snowflake_user": self.snowflake_config["user"],
                "snowflake_database": self.snowflake_config["database"],
            }
        )

        self._conn = None
        self._conn_lock = asyncio.Lock()
        self._ready_schemas = set()

        # Register for config push notifications
        self.register_config_handler(self.on_collection_config, types=["collection"])

    async def _get_connection(self):
        async with self._conn_lock:
            if self._conn is None:
                import snowflake.connector

                self._conn = await asyncio.to_thread(
                    snowflake.connector.connect, **self.snowflake_config,
                )
            return self._conn

    async def _ensure_schema(self, workspace):
        schema = _safe_ident(workspace)
        if schema in self._ready_schemas:
            return schema

        conn = await self._get_connection()

        def _create():
            cur = conn.cursor()
            try:
                cur.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')
                cur.execute(
                    f'CREATE TABLE IF NOT EXISTS "{schema}"."{TABLE_NAME}" ('
                    'COLLECTION STRING, S STRING, P STRING, O STRING, '
                    'G STRING, OTYPE STRING, DTYPE STRING, LANG STRING)'
                )
            finally:
                cur.close()

        await asyncio.to_thread(_create)
        self._ready_schemas.add(schema)
        return schema

    async def store_triples(self, workspace, message):

        schema = await self._ensure_schema(workspace)
        conn = await self._get_connection()

        rows = []
        for t in message.triples:
            s_val = get_term_value(t.s)
            p_val = get_term_value(t.p)
            o_val = get_term_value(t.o)
            g_val = t.g if t.g is not None else DEFAULT_GRAPH

            rows.append((
                message.metadata.collection,
                s_val, p_val, o_val, g_val,
                get_term_otype(t.o), get_term_dtype(t.o), get_term_lang(t.o),
            ))

        if not rows:
            return

        def _insert():
            cur = conn.cursor()
            try:
                cur.executemany(
                    f'INSERT INTO "{schema}"."{TABLE_NAME}" '
                    '(COLLECTION, S, P, O, G, OTYPE, DTYPE, LANG) '
                    'VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
                    rows,
                )
            finally:
                cur.close()

        await asyncio.to_thread(_insert)

    async def create_collection(self, workspace: str, collection: str, metadata: dict):
        """Collections are modeled as a column value, not a physical
        object, so simply ensure the underlying schema/table exist."""
        await self._ensure_schema(workspace)
        logger.info(f"Collection {collection} ready in workspace {workspace}")

    async def delete_collection(self, workspace: str, collection: str):
        schema = await self._ensure_schema(workspace)
        conn = await self._get_connection()

        def _delete():
            cur = conn.cursor()
            try:
                cur.execute(
                    f'DELETE FROM "{schema}"."{TABLE_NAME}" WHERE COLLECTION = %s',
                    (collection,),
                )
            finally:
                cur.close()

        try:
            await asyncio.to_thread(_delete)
            logger.info(f"Deleted all triples for collection {collection} from schema {schema}")
        except Exception as e:
            logger.error(f"Failed to delete collection {workspace}/{collection}: {e}", exc_info=True)
            raise

    @staticmethod
    def add_args(parser):

        TriplesStoreService.add_args(parser)
        add_snowflake_args(parser)

def run():

    Processor.launch(default_ident, __doc__)
