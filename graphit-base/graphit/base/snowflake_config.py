"""
Snowflake configuration utilities for standardized parameter handling.

Provides consistent Snowflake configuration across all GraphIt processors,
including command-line arguments, environment variables, and defaults.
"""

import os
import argparse
from typing import Optional, Any


def get_snowflake_defaults() -> dict:
    """
    Get default Snowflake configuration values from environment variables.

    Returns:
        dict: Dictionary with 'account', 'user', 'password', 'warehouse',
        'database' and 'role' keys.
    """
    return {
        'account': os.getenv('SNOWFLAKE_ACCOUNT'),
        'user': os.getenv('SNOWFLAKE_USER'),
        'password': os.getenv('SNOWFLAKE_PASSWORD'),
        'warehouse': os.getenv('SNOWFLAKE_WAREHOUSE'),
        'database': os.getenv('SNOWFLAKE_DATABASE', 'GRAPHIT'),
        'role': os.getenv('SNOWFLAKE_ROLE'),
    }


def add_snowflake_args(parser: argparse.ArgumentParser) -> None:
    """
    Add standardized Snowflake configuration arguments to an argument parser.

    Shows environment variable values in help text when they are set.
    Password values are never displayed for security.

    Args:
        parser: ArgumentParser instance to add arguments to
    """
    defaults = get_snowflake_defaults()

    def help_for(name, env_name, value, secret=False):
        text = name
        if value:
            text += f" (default: {'<set>' if secret else value})"
            if env_name in os.environ:
                text += f" [from {env_name}]"
        return text

    parser.add_argument(
        '--snowflake-account',
        default=defaults['account'],
        help=help_for(
            "Snowflake account identifier", 'SNOWFLAKE_ACCOUNT',
            defaults['account'],
        ),
    )

    parser.add_argument(
        '--snowflake-user',
        default=defaults['user'],
        help=help_for("Snowflake username", 'SNOWFLAKE_USER', defaults['user']),
    )

    parser.add_argument(
        '--snowflake-password',
        default=defaults['password'],
        help=help_for(
            "Snowflake password", 'SNOWFLAKE_PASSWORD', defaults['password'],
            secret=True,
        ),
    )

    parser.add_argument(
        '--snowflake-warehouse',
        default=defaults['warehouse'],
        help=help_for(
            "Snowflake warehouse", 'SNOWFLAKE_WAREHOUSE', defaults['warehouse'],
        ),
    )

    parser.add_argument(
        '--snowflake-database',
        default=defaults['database'],
        help=help_for(
            "Snowflake database", 'SNOWFLAKE_DATABASE', defaults['database'],
        ),
    )

    parser.add_argument(
        '--snowflake-role',
        default=defaults['role'],
        help=help_for("Snowflake role", 'SNOWFLAKE_ROLE', defaults['role']),
    )


def resolve_snowflake_config(
    args: Optional[Any] = None,
    account: Optional[str] = None,
    user: Optional[str] = None,
    password: Optional[str] = None,
    warehouse: Optional[str] = None,
    database: Optional[str] = None,
    role: Optional[str] = None,
) -> dict:
    """
    Resolve Snowflake connection settings from explicit args, parsed CLI
    args, and environment variables (in that priority order).

    Returns:
        dict: kwargs suitable for `snowflake.connector.connect(**config)`.
    """
    if args is not None:
        account = account or getattr(args, 'snowflake_account', None)
        user = user or getattr(args, 'snowflake_user', None)
        password = password or getattr(args, 'snowflake_password', None)
        warehouse = warehouse or getattr(args, 'snowflake_warehouse', None)
        database = database or getattr(args, 'snowflake_database', None)
        role = role or getattr(args, 'snowflake_role', None)

    defaults = get_snowflake_defaults()
    account = account or defaults['account']
    user = user or defaults['user']
    password = password or defaults['password']
    warehouse = warehouse or defaults['warehouse']
    database = database or defaults['database']
    role = role or defaults['role']

    if not account or not user or not password:
        raise RuntimeError(
            "Snowflake account, user and password must be configured via "
            "--snowflake-* arguments or SNOWFLAKE_* environment variables"
        )

    config = {
        'account': account,
        'user': user,
        'password': password,
        'database': database,
    }
    if warehouse:
        config['warehouse'] = warehouse
    if role:
        config['role'] = role

    return config
