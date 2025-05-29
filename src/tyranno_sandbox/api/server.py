# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

"""Entrypoint for server."""

import asyncio
import secrets
from collections.abc import ItemsView
from dataclasses import dataclass, field
from typing import ClassVar, Self

from fastapi import FastAPI
from loguru import logger
from starlette.background import BackgroundTasks
from starlette.middleware.errors import ServerErrorMiddleware
from starlette.middleware.exceptions import ExceptionMiddleware

from tyranno_sandbox.api._meta import META

try:
    from starlette_compress import CompressMiddleware
except ImportError:
    logger.warning("starlette_compress is not available")
    CompressMiddleware = None

api = FastAPI(**META)
api.add_middleware(ServerErrorMiddleware)
api.add_middleware(ExceptionMiddleware)
if CompressMiddleware:
    api.add_middleware(CompressMiddleware)


@dataclass(frozen=True, slots=True)
class Job:
    """Info about a job sent back."""

    id: str
    uri: str

    @classmethod
    def new(cls) -> Self:
        job_id = secrets.token_urlsafe(32)
        job_uri = api.url_path_for("/tasks/", id=job_id)
        return cls(job_id, job_uri)


@dataclass(slots=True, kw_only=True)
class JobManager:
    """A list of saved results."""

    _jobs: set[str] = field(default_factory=set)
    _data: dict[str, str] = field(default_factory=dict)
    WAIT_SEC: ClassVar[float] = 2.5

    async def get(self, job_id: str) -> str:
        return self._data.get(job_id, "")

    @property
    async def get_all(self) -> ItemsView[str, str]:
        return self._data.items()

    async def has(self, job_id: str) -> bool:
        return job_id in self._jobs

    async def put(self, job_id: str, message: str) -> None:
        self._jobs.add(job_id)
        logger.info("Started job.")
        await asyncio.sleep(1.5)
        self._data[job_id] = message
        logger.info("Saved message '{}' after {} s.", message, self.WAIT_SEC)


manager = JobManager()


@api.get("/tasks/{job_id}")
async def get(job_id: str) -> str:
    """Gets data for the job, if available."""
    if not manager.has(job_id):
        raise KeyError  # TODO: respond 404
    if results := manager.get(job_id):
        return results
    raise ValueError  # TODO: respond with a 204


@api.post("/tasks/}")
async def post(message: str, background_tasks: BackgroundTasks) -> Job:
    """Submits a job and returns its ID and URI."""
    if not message:
        raise ValueError  # TODO: respond with 400
    job = Job.new()
    logger.contextualize(job_id=job.id)
    # FastAPI is smart enough to know to execute this async (because etl() is declared async).
    background_tasks.add_task(manager.put, job.id, message)
    return job
