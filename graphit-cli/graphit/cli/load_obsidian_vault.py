"""
Loads a folder of Obsidian markdown notes into the library and starts
processing them through the named flow (the flow blueprint wired to the
obsidian-decoder, triples-write-snowflake and text-completion-cortex
processors).
"""

import argparse
import fnmatch
import os
import uuid

from graphit.api import Api
from graphit.knowledge import hash, to_uri, PREF_DOC

default_url = os.getenv("GRAPHIT_URL", 'http://localhost:8088/')
default_token = os.getenv("GRAPHIT_TOKEN", None)
default_workspace = os.getenv("GRAPHIT_WORKSPACE", "default")

# Skip Obsidian's "not content" convention (underscore-prefixed folders)
# and common meta/instruction files by default.
DEFAULT_EXCLUDES = ["_*/*", "CLAUDE.md", "*README*.md"]


def _is_excluded(rel_path, patterns):
    rel_path = rel_path.replace(os.sep, "/").lower()
    name = os.path.basename(rel_path)
    return any(
        fnmatch.fnmatch(rel_path, pat.lower()) or fnmatch.fnmatch(name, pat.lower())
        for pat in patterns
    )


def _inject_vault_folder(text, rel_dir):
    """Stamp the note's vault-relative folder onto its frontmatter (as a
    'vault-folder' field) so it's recoverable as a graph property even
    when a note's own frontmatter doesn't already capture domain/type."""

    rel_dir = rel_dir.replace(os.sep, "/")
    if rel_dir in ("", "."):
        return text

    escaped = rel_dir.replace('"', '\\"')
    line = f'vault-folder: "{escaped}"\n'

    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end != -1:
            insert_at = end + 1
            return text[:insert_at] + line + text[insert_at:]

    return f"---\n{line}---\n{text}"


class Loader:

    def __init__(
            self, url, flow, collection, tags, exclude=None,
            token=None, workspace="default",
    ):

        self.api = Api(url, token=token, workspace=workspace).library()
        self.flow = flow
        self.collection = collection
        self.tags = tags.split(",") if tags else []
        self.excludes = list(DEFAULT_EXCLUDES) + (exclude.split(",") if exclude else [])

    def load(self, vault):

        for root, dirs, files in os.walk(vault):
            for name in files:
                if not name.lower().endswith(".md"):
                    continue

                path = os.path.join(root, name)
                rel_path = os.path.relpath(path, vault)

                if _is_excluded(rel_path, self.excludes):
                    print(f"{path}: Skipped (excluded).")
                    continue

                self.load_file(path, os.path.dirname(rel_path))

    def load_file(self, path, rel_dir):

        try:

            text = open(path, "r", encoding="utf-8").read()
            text = _inject_vault_folder(text, rel_dir)
            data = text.encode("utf-8")

            id = to_uri(PREF_DOC, hash(data))
            title = os.path.splitext(os.path.basename(path))[0]

            self.api.add_document(
                document=data, id=id, metadata=None,
                title=title, comments=None,
                kind="text/markdown", tags=self.tags,
            )

            self.api.start_processing(
                id=str(uuid.uuid4()),
                document_id=id,
                flow=self.flow,
                collection=self.collection,
                tags=self.tags,
            )

            print(f"{path}: Loaded successfully.")

        except Exception as e:
            print(f"{path}: Failed: {str(e)}", flush=True)
            raise e


def main():

    parser = argparse.ArgumentParser(
        prog='gr-load-obsidian-vault',
        description=__doc__,
    )

    parser.add_argument(
        '-u', '--url',
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
        '-i', '--flow-id',
        default="obsidian",
        help='Flow ID wired to the obsidian-decoder (default: obsidian)',
    )

    parser.add_argument(
        '--collection',
        default='default',
        help='Collection (default: default)',
    )

    parser.add_argument(
        '--tags',
        help='Tags, comma separated',
    )

    parser.add_argument(
        '--exclude',
        help=(
            'Extra glob patterns to skip, comma separated, matched against '
            'each note\'s vault-relative path or filename (in addition to '
            'the defaults: ' + ", ".join(DEFAULT_EXCLUDES) + ')'
        ),
    )

    parser.add_argument(
        'vault',
        help='Path to the Obsidian vault folder',
    )

    args = parser.parse_args()

    try:

        loader = Loader(
            url=args.url,
            flow=args.flow_id,
            collection=args.collection,
            tags=args.tags,
            exclude=args.exclude,
            token=args.token,
            workspace=args.workspace,
        )

        loader.load(args.vault)

    except Exception as e:

        print("Exception:", e, flush=True)


if __name__ == "__main__":
    main()
