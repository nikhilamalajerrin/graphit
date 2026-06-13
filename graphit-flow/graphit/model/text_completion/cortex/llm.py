
"""
Simple LLM service, performs text prompt completion using Snowflake
Cortex (SNOWFLAKE.CORTEX.COMPLETE), so existing GraphIt services
(agent-orchestrator, GraphRAG, kg-extract-*) can reason over data using
Cortex instead of an external LLM provider.
"""

import asyncio
import logging

from .... exceptions import LlmError
from .... base import LlmService, LlmResult
from .... base.snowflake_config import add_snowflake_args, resolve_snowflake_config

# Module logger
logger = logging.getLogger(__name__)

default_ident = "text-completion"

default_model = "mistral-large2"
default_temperature = 0.0


class Processor(LlmService):

    def __init__(self, **params):

        model = params.get("model", default_model)
        temperature = params.get("temperature", default_temperature)

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
                "model": model,
                "temperature": temperature,
                "snowflake_account": self.snowflake_config["account"],
                "snowflake_user": self.snowflake_config["user"],
                "snowflake_database": self.snowflake_config["database"],
            }
        )

        self.default_model = model
        self.temperature = temperature

        self._conn = None
        self._conn_lock = asyncio.Lock()

        logger.info("Snowflake Cortex LLM service initialized")

    async def _get_connection(self):
        async with self._conn_lock:
            if self._conn is None:
                import snowflake.connector

                self._conn = await asyncio.to_thread(
                    snowflake.connector.connect, **self.snowflake_config,
                )
            return self._conn

    async def generate_content(self, system, prompt, model=None, temperature=None):

        model_name = model or self.default_model
        combined_prompt = f"{system}\n\n{prompt}"

        logger.debug(f"Using Cortex model: {model_name}")

        conn = await self._get_connection()

        def _complete():
            cur = conn.cursor()
            try:
                cur.execute(
                    "SELECT SNOWFLAKE.CORTEX.COMPLETE(%s, %s)",
                    (model_name, combined_prompt),
                )
                row = cur.fetchone()
                return row[0] if row else ""
            finally:
                cur.close()

        try:
            text = await asyncio.to_thread(_complete)

            logger.debug(f"Cortex response: {text}")

            return LlmResult(
                text=text,
                # Cortex's single-string COMPLETE form does not report
                # token usage; leave unset like other providers that
                # don't report it.
                in_token=None,
                out_token=None,
                model=model_name,
            )

        except Exception as e:

            logger.error(f"Cortex LLM exception ({type(e).__name__}): {e}", exc_info=True)
            raise LlmError() from e

    @staticmethod
    def add_args(parser):

        LlmService.add_args(parser)

        parser.add_argument(
            '-m', '--model',
            default=default_model,
            help=f'Cortex model (default: {default_model})'
        )

        parser.add_argument(
            '-t', '--temperature',
            type=float,
            default=default_temperature,
            help=f'LLM temperature parameter (default: {default_temperature})'
        )

        add_snowflake_args(parser)


def run():

    Processor.launch(default_ident, __doc__)
