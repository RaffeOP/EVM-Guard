"""Resolve catalog paths against the repository root.

Catalogs store paths relative to the repository root, so a clone in any directory
can run the evaluation. Absolute paths are accepted unchanged for older catalogs.
"""
import os

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def resolve(path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(REPO, path)


def relative(path: str) -> str:
    return os.path.relpath(path, REPO) if os.path.isabs(path) else path
