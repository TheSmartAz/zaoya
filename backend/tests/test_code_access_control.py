import asyncio
from uuid import uuid4

import pytest
from fastapi import HTTPException
from types import SimpleNamespace

from app.api.files import _get_project_or_403


class _Result:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class _Session:
    def __init__(self, value):
        self._value = value

    async def execute(self, *args, **kwargs):
        return _Result(self._value)


def test_code_access_allows_owner():
    owner_id = uuid4()
    project = SimpleNamespace(id=uuid4(), owner_id=owner_id)

    async def run():
        result = await _get_project_or_403(str(project.id), owner_id, _Session(project))
        assert result == project

    asyncio.run(run())


def test_code_access_denies_non_owner():
    owner_id = uuid4()
    viewer_id = uuid4()
    project = SimpleNamespace(id=uuid4(), owner_id=owner_id)

    async def run():
        with pytest.raises(HTTPException) as excinfo:
            await _get_project_or_403(str(project.id), viewer_id, _Session(project))
        assert excinfo.value.status_code == 403

    asyncio.run(run())
