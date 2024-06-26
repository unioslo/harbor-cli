"""Tests for models from the harborapi package.

In certain places, we take advantage of custom validators on
the models from the package to perform things like type coercion
and extra validation.

These tests ensure that the custom validators work as expected."""

from __future__ import annotations

import pytest
from harborapi.models import ProjectMetadata


@pytest.mark.parametrize("inp,expect", [(True, "true"), (False, "false"), (None, None)])
def test_project_metadata_bool_to_string(inp: bool, expect: str | None) -> None:
    """Test that the project metadata model can convert a bool to a string."""
    metadata = ProjectMetadata(
        # validator does bool -> str conversion for the string bool fields
        public=inp,
        enable_content_trust=inp,
        enable_content_trust_cosign=inp,
        prevent_vul=inp,
        auto_scan=inp,
        reuse_sys_cve_allowlist=inp,
        auto_sbom_generation=inp,
    )
    assert metadata.public == expect
    assert metadata.enable_content_trust == expect
    assert metadata.enable_content_trust_cosign == expect
    assert metadata.prevent_vul == expect
    assert metadata.auto_scan == expect
    assert metadata.reuse_sys_cve_allowlist == expect
    assert metadata.auto_sbom_generation == expect

    # Test with dict input
    metadata_from_dict = ProjectMetadata.model_validate(
        {
            "public": inp,
            "enable_content_trust": inp,
            "enable_content_trust_cosign": inp,
            "prevent_vul": inp,
            "auto_scan": inp,
            "reuse_sys_cve_allowlist": inp,
            "auto_sbom_generation": inp,
        }
    )
    assert metadata == metadata_from_dict
