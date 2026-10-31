"""The shared fixtures match what the pipeline makes now (regenerate with python -m tests.busyness.fixtures)."""

import json

import pytest

from .fixtures import CASES, FIXTURES, make


@pytest.mark.parametrize("name", CASES)
def test_fixture_is_current(name):
    on_disk = json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))
    assert on_disk == json.loads(json.dumps(make(name))), f"regenerate: python -m tests.busyness.fixtures ({name})"
