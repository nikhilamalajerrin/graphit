
"""
Triples query service.  Input is a (s, p, o, g) quad pattern, some values
may be null.  Output is a list of quads.  Reads from a Snowflake table.
"""

import re
import json
import asyncio
import logging

from .... schema import Term, Triple, IRI, LITERAL, TRIPLE, BLANK
from .... base import TriplesQueryService
from .... base.snowflake_config import add_snowflake_args, resolve_snowflake_config

# Module logger
logger = logging.getLogger(__name__)

default_ident = "triples-query"

DEFAULT_GRAPH = ""

TABLE_NAME = "TRIPLES"


def _safe_ident(name):
    safe = re.sub(r"[^A-Za-z0-9_]", "_", name or "") or "DEFAULT"
    return safe.upper()


def serialize_triple(triple):
    """Serialize a Triple object to JSON (must match storage format)."""
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


def create_term(value, term_type=None, datatype=None, language=None):
    """Create a Term from a stored string value plus its otype/dtype/lang."""
    if term_type == 'u':
        return Term(type=IRI, iri=value)
    elif term_type == 'l':
        return Term(
            type=LITERAL,
            value=value,
            datatype=datatype or "",
            language=language or "",
        )
    elif term_type == 't':
        try:
            triple_data = json.loads(value) if isinstance(value, str) else value
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"Failed to parse triple JSON: {e}")
            return Term(type=LITERAL, value=str(value))
        if isinstance(triple_data, dict):

            def deserialize_term(term_dict):
                if term_dict is None:
                    return None
                tt = term_dict.get("type", "")
                if tt == IRI:
                    return Term(type=IRI, iri=term_dict.get("iri", ""))
                elif tt == LITERAL:
                    return Term(
                        type=LITERAL,
                        value=term_dict.get("value", ""),
                        datatype=term_dict.get("datatype", ""),
                        language=term_dict.get("language", ""),
                    )
                elif tt == TRIPLE:
                    nested = term_dict.get("triple")
                    if nested:
                        return Term(
                            type=TRIPLE,
                            triple=Triple(
                                s=deserialize_term(nested.get("s")),
                                p=deserialize_term(nested.get("p")),
                                o=deserialize_term(nested.get("o")),
                            ),
                        )
                return Term(type=LITERAL, value=str(term_dict))

            return Term(
                type=TRIPLE,
                triple=Triple(
                    s=deserialize_term(triple_data.get("s")),
                    p=deserialize_term(triple_data.get("p")),
                    o=deserialize_term(triple_data.get("o")),
                ),
            )
        return Term(type=LITERAL, value=str(value))

    # Heuristic fallback
    if value and (value.startswith("http://") or value.startswith("https://")):
        return Term(type=IRI, iri=value)
    return Term(type=LITERAL, value=value)


class Processor(TriplesQueryService):

    def __init__(self, **params):

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

    async def _get_connection(self):
        async with self._conn_lock:
            if self._conn is None:
                import snowflake.connector

                self._conn = await asyncio.to_thread(
                    snowflake.connector.connect, **self.snowflake_config,
                )
            return self._conn

    async def query_triples(self, workspace, query):

        try:
            schema = _safe_ident(workspace)
            conn = await self._get_connection()

            s_val = get_term_value(query.s)
            p_val = get_term_value(query.p)
            o_val = get_term_value(query.o)
            g_val = query.g

            clauses = ["COLLECTION = %s"]
            params = [query.collection]

            if s_val is not None:
                clauses.append("S = %s")
                params.append(s_val)
            if p_val is not None:
                clauses.append("P = %s")
                params.append(p_val)
            if o_val is not None:
                clauses.append("O = %s")
                params.append(o_val)
            if g_val is not None:
                clauses.append("G = %s")
                params.append(g_val)

            sql = (
                f'SELECT S, P, O, G, OTYPE, DTYPE, LANG FROM "{schema}"."{TABLE_NAME}" '
                f'WHERE {" AND ".join(clauses)}'
            )
            if query.limit and query.limit > 0:
                sql += f" LIMIT {int(query.limit)}"

            def _select():
                cur = conn.cursor()
                try:
                    cur.execute(sql, params)
                    return cur.fetchall()
                except Exception as e:
                    # Table/schema not created yet for this workspace -
                    # equivalent to "no results" rather than an error.
                    if "does not exist" in str(e).lower():
                        return []
                    raise
                finally:
                    cur.close()

            rows = await asyncio.to_thread(_select)

            triples = [
                Triple(
                    s=create_term(row[0], term_type='u'),
                    p=create_term(row[1], term_type='u'),
                    o=create_term(row[2], term_type=row[4], datatype=row[5], language=row[6]),
                    g=row[3] if row[3] != DEFAULT_GRAPH else None,
                )
                for row in rows
            ]

            return triples

        except Exception as e:

            logger.error(f"Exception querying triples: {e}", exc_info=True)
            raise e

    @staticmethod
    def add_args(parser):

        TriplesQueryService.add_args(parser)
        add_snowflake_args(parser)


def run():

    Processor.launch(default_ident, __doc__)
