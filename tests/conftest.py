"""Shared pytest setup.

Chroma's PersistentClient keeps its sqlite file open for the life of the process,
so on Windows the fixtures' own `shutil.rmtree` can silently fail and leave a
`storage/test_*` directory behind after every run. Cleaning them at session start
(where no client exists yet) keeps the workspace tidy without weakening teardown.
"""
import shutil
from pathlib import Path

_STORAGE = Path(__file__).resolve().parent.parent / "storage"


def pytest_sessionstart(session):
    if not _STORAGE.is_dir():
        return
    for path in _STORAGE.glob("test_*"):
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
