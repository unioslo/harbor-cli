from __future__ import annotations

import json
from datetime import datetime
from datetime import timezone
from pathlib import Path

from harborapi.ext import ArtifactInfo
from harborapi.models.models import Artifact
from harborapi.models.models import ScheduleObj

from harbor_cli.output.schema import Schema


def test_schema_deserialization() -> None:
    """Test deserialization of Schema."""
    scheduleobj_data = {
        # these are likely mutually exclusive in practice, but
        # just test them all in one go
        "type": "Hourly",
        "cron": "0 0 * * * *",
        "next_scheduled_time": "2021-08-31T14:00:00Z",
    }

    data = {
        "version": "1.0.0",
        "type_": "ScheduleObj",
        "data": scheduleobj_data,
    }
    schema = Schema(**data)
    assert schema.data == scheduleobj_data
    schema.update_data_type()
    assert isinstance(schema.data, ScheduleObj)
    assert isinstance(schema.data.next_scheduled_time, datetime)


def test_schema_from_file() -> None:
    p = Path(__file__).parent / "data/schema_artifact.json"
    schema = Schema.from_file(p)
    assert isinstance(schema.data, Artifact)
    d = schema.data
    assert d.id == 1234
    assert d.project_id == 123
    assert d.repository_id == 456
    assert d.digest == "sha256:1234567890abcdef"
    assert d.size == 1234567890
    assert d.extra_attrs.architecture == "amd64"
    assert d.extra_attrs.config["ExposedPorts"] == {"8080/tcp": {}}

    d_dict = json.loads(p.read_text())
    assert schema.data == Artifact(**d_dict["data"])


def test_schema_from_file_ext() -> None:
    p = Path(__file__).parent / "data/schema_artifactinfo.json"
    schema = Schema.from_file(p)
    assert isinstance(schema.data, ArtifactInfo)

    d = schema.data
    assert d.artifact.id == 1234
    assert d.artifact.project_id == 123
    assert d.artifact.repository_id == 456
    assert d.artifact.digest == "sha256:1234567890abcdef"
    assert d.artifact.size == 1234567890
    assert d.artifact.extra_attrs.architecture == "amd64"
    assert d.artifact.extra_attrs.config["ExposedPorts"] == {"8080/tcp": {}}

    assert d.repository.project_id == 123
    assert d.repository.id == 456
    assert d.repository.name == "test-project/test-repo"
    assert d.repository.description is None
    assert d.repository.artifact_count == 100
    assert d.repository.pull_count == 999
    assert d.repository.creation_time == datetime(
        2022, 1, 1, 1, 2, 3, tzinfo=timezone.utc
    )
    assert d.repository.update_time == datetime(
        2022, 2, 2, 1, 2, 3, tzinfo=timezone.utc
    )

    d_dict = json.loads(p.read_text())
    assert schema.data == ArtifactInfo(**d_dict["data"])
