from __future__ import annotations


def test_sample_config(invoke):
    result = invoke(["sample-config"])
    assert result.exit_code == 0
    assert result.stdout.endswith("\n")
    assert not result.stdout.endswith("\n\n")
