import json
import pytest
from app.agents.evaluate import DATASET, run_case


@pytest.mark.parametrize("case", json.loads(DATASET.read_text()), ids=lambda x: x["id"])
def test_offline_evaluation(case):
    assert run_case(case)["passed"]
