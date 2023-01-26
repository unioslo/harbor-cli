from __future__ import annotations


def test_sample_config(invoke):
    result = invoke(["sample-config"])
    assert result.exit_code == 0
