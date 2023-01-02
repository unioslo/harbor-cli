from __future__ import annotations

import json
from datetime import datetime
from datetime import timezone
from pathlib import Path

from harborapi.ext import ArtifactInfo
from harborapi.models.models import Artifact
from harborapi.models.models import ScheduleObj

from harbor_cli.output.schema import Schema


def test_schema_init() -> None:
    """Test deserialization of Schema."""
    schedule = ScheduleObj(
        # these are likely mutually exclusive in practice, but
        # just test them all in one go
        type="Hourly",
        cron="0 0 * * * *",
        next_scheduled_time="2021-08-31T14:00:00Z",
    )

    # Using __init__
    schema = Schema(data=schedule)  # type: Schema[ScheduleObj]
    assert schema.data == schedule
    assert isinstance(schema.data, ScheduleObj)
    assert isinstance(schema.data.next_scheduled_time, datetime)

    # Using from_data classmethod (preferred)
    schema2 = Schema.from_data(schedule)
    assert schema2 == schema


def test_schema_serialization() -> None:
    """Test serialization of Schema."""
    schedule = ScheduleObj(
        type="Hourly",
        cron="0 0 * * * *",
        next_scheduled_time="2021-08-31T14:00:00+00:00",
    )

    schema = Schema.from_data(schedule)
    # Serialize to JSON, so we can test the string representation
    # of the different values. If we just use .dict(), we still
    # have to deal with Python objects (e.g. datetime)
    schema_dict = json.loads(schema.json())
    assert schema_dict["data"]["type"] == "Hourly"
    assert schema_dict["data"]["cron"] == "0 0 * * * *"
    assert schema_dict["data"]["next_scheduled_time"] == "2021-08-31T14:00:00+00:00"
    assert schema_dict["version"] == "1.0.0"
    assert schema_dict["type"] == "ScheduleObj"
    assert schema_dict["module"] == "harborapi.models.models"


def test_schema_deserialization() -> None:
    """Test deserialization of Schema."""
    schedule = ScheduleObj(
        type="Hourly",
        cron="0 0 * * * *",
        next_scheduled_time="2021-08-31T14:00:00+00:00",
    )
    schema = Schema.from_data(schedule)
    # Serialize to JSON and then deserialize back to Schema
    schema_dict = json.loads(schema.json())
    schema2 = Schema(**schema_dict)
    assert schema2 == schema
    assert schema2.data == schedule
    assert isinstance(schema2.data, ScheduleObj)
    assert isinstance(schema2.data.next_scheduled_time, datetime)


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


def test_schema_non_basemodel() -> None:
    """Test Schema with non-BaseModel data."""
    s = Schema.from_data("hello, world")
    assert s.data == "hello, world"
    assert s.type == "str"
    assert s.module == "builtins"

    s2 = Schema(
        data="hello, world",
    )  # type: Schema[str]
    assert s == s2
