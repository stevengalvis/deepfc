"""Public consumer examples must never pass the genuine-data boundary."""
import json
from pathlib import Path

import pytest
from experiments import research_exchange as exchange


def test_public_examples_cannot_be_ingested_as_genuine():
    path = Path(__file__).resolve().parents[1] / 'experiments/contracts/team_goals_v1/examples/SYNTHETIC_ONLY.json'
    examples = json.loads(path.read_text())
    assert examples['environment'] == 'synthetic_test'
    assert {r['fixture']['competition'] for r in examples['records']} == set(exchange.LEAGUES)
    for record in examples['records']:
        assert record['environment'] == 'synthetic_test'
        with pytest.raises(exchange.core.Invalid, match='synthetic/production'):
            exchange.validate_record(record)
