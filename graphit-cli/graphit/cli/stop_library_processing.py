"""
Removes a library document processing record.  This is just a record of
procesing, it doesn't stop in-flight processing at the moment.
"""

import argparse
import os
from graphit.api import Api

default_url = os.getenv("GRAPHIT_URL", 'http://localhost:8088/')
default_token = os.getenv("GRAPHIT_TOKEN", None)
default_workspace = os.getenv("GRAPHIT_WORKSPACE", "default")

def stop_processing(url, id, token=None, workspace="default"):

    api = Api(url, token=token, workspace=workspace).library()

    api.stop_processing(id=id)

def main():

    parser = argparse.ArgumentParser(
        prog='gr-stop-library-processing',
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
        '--id', '--processing-id',
        required=True,
        help=f'Processing ID',
    )

    args = parser.parse_args()

    try:

        stop_processing(
            url=args.api_url,
            id=args.id,
            token=args.token,
            workspace=args.workspace,
        )

    except Exception as e:

        print("Exception:", e, flush=True)

if __name__ == "__main__":
    main()
