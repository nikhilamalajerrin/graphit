"""
Uploads a flow blueprint definition.  You can take the output of
gr-get-flow-blueprint and load it back in using this utility.
"""

import argparse
import os
from graphit.api import Api
import json

default_url = os.getenv("GRAPHIT_URL", 'http://localhost:8088/')
default_token = os.getenv("GRAPHIT_TOKEN", None)
default_workspace = os.getenv("GRAPHIT_WORKSPACE", "default")

def put_flow_blueprint(url, blueprint_name, config, token=None,
                       workspace="default"):

    api = Api(url, token=token, workspace=workspace)

    blueprint_names = api.flow().put_blueprint(blueprint_name, config)

def main():

    parser = argparse.ArgumentParser(
        prog='gr-put-flow-blueprint',
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

    parser.add_argument(
        '-n', '--blueprint-name',
        help=f'Flow blueprint name',
    )

    parser.add_argument(
        '-c', '--config',
        help=f'Initial configuration to load, should be raw JSON',
    )

    args = parser.parse_args()

    try:

        put_flow_blueprint(
            url=args.api_url,
            blueprint_name=args.blueprint_name,
            config=json.loads(args.config),
            token=args.token,
            workspace=args.workspace,
        )

    except Exception as e:

        print("Exception:", e, flush=True)

if __name__ == "__main__":
    main()
