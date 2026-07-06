from __future__ import annotations  # makes all annotations strings at runtime

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from cappuccino2.users.models import User  # only used during type checking

from cappuccino2.users.tests.factories import UserFactory

if TYPE_CHECKING:
    from cappuccino2.users.models import User


@pytest.fixture(autouse=True)
def _media_storage(settings, tmpdir) -> None:
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture
def user(db) -> User:
    return UserFactory.create()
