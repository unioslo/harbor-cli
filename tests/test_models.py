from __future__ import annotations

import pytest

from harbor_cli.models import MemberRoleType
from harbor_cli.models import UserGroupType


def test_user_group_type_from_int() -> None:
    assert UserGroupType.from_int(1) == UserGroupType.LDAP
    assert UserGroupType.from_int(2) == UserGroupType.HTTP
    assert UserGroupType.from_int(3) == UserGroupType.OIDC


def test_user_group_type_from_int_invalid() -> None:
    with pytest.raises(ValueError) as excinfo:
        UserGroupType.from_int(4)
    assert "4" in str(excinfo.value)


def test_user_group_type_as_int() -> None:
    assert UserGroupType.LDAP.as_int() == 1
    assert UserGroupType.HTTP.as_int() == 2
    assert UserGroupType.OIDC.as_int() == 3
    assert len(UserGroupType) == 3  # ensures we keep this test up to date


def test_member_role_type_from_int() -> None:
    assert MemberRoleType.from_int(1) == MemberRoleType.ADMIN
    assert MemberRoleType.from_int(2) == MemberRoleType.DEVELOPER
    assert MemberRoleType.from_int(3) == MemberRoleType.GUEST
    assert MemberRoleType.from_int(4) == MemberRoleType.MAINTAINER
    assert MemberRoleType.from_int(5) == MemberRoleType.LIMITED_GUEST
    assert len(MemberRoleType) == 5  # ensures we keep this test up to date


def test_member_role_type_from_int_invalid() -> None:
    with pytest.raises(ValueError) as excinfo:
        MemberRoleType.from_int(6)
    assert "6" in str(excinfo.value)


def test_member_role_type_as_int() -> None:
    assert MemberRoleType.ADMIN.as_int() == 1
    assert MemberRoleType.DEVELOPER.as_int() == 2
    assert MemberRoleType.GUEST.as_int() == 3
    assert MemberRoleType.MAINTAINER.as_int() == 4
