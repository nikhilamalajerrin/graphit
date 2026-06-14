"""
Dumps out the current configuration
"""

import argparse
import os
from graphit.api import Api
import json

default_url = os.getenv("GRAPHIT_URL", 'http://localhost:8088/')
default_token = os.getenv("GRAPHIT_TOKEN", None)
default_workspace = os.getenv("GRAPHIT_WORKSPACE", "default")

def show_config(url, token=None, workspace="default"):

    api = Api(url, token=token, workspace=workspace).config()

    config, version = api.all()

    print("Version:", version)
    print(json.dumps(config, indent=4))

def main():

    parser = argparse.ArgumentParser(
        prog='gr-show-config',
        description=__doc__,
    )

    parser.add_argument(
        '-u', '--api-url',
        default=default_url,
        help=f'API URL (default: {default_url})',
    )

    parser.add_argument(
        '-t', '--token',
        default=default_token,
        help='Authentication token (default: $GRAPHIT_TOKEN)',
    )

    parser.add_argument(
        '-w', '--workspace',
        default=default_workspace,
        help=f'Workspace (default: {default_workspace})',
    )

    args = parser.parse_args()

    try:

        show_config(
            url=args.api_url,
            token=args.token,
            workspace=args.workspace,
        )

    except Exception as e:

        print("Exception:", e, flush=True)

if __name__ == "__main__":
    main()