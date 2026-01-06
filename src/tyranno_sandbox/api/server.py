# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0

"""Entrypoint for server."""

import asyncio
import secrets
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Self

from fastapi import BackgroundTasks, FastAPI, HTTPException, Response, status
from loguru import logger
from starlette.middleware.errors import ServerErrorMiddleware
from starlette.middleware.exceptions import ExceptionMiddleware
from starlette_compress import CompressMiddleware

from tyranno_sandbox.api._meta import META

if TYPE_CHECKING:
    from collections.abc import ItemsView

api = FastAPI(**META)
api.add_middleware(ServerErrorMiddleware)
api.add_middleware(ExceptionMiddleware)
api.add_middleware(CompressMiddleware)


@dataclass(frozen=True, slots=True)
class Job:
    """Identifier + canonical URI for a queued job (used as a response model)."""

    id: str
    uri: str

    @classmethod
    def new(cls, *, endpoint_name: str) -> Self:
        job_id = secrets.token_urlsafe(16)
        job_uri = api.url_path_for(endpoint_name, job_id=job_id)
        return cls(job_id, job_uri)


@dataclass(slots=True, kw_only=True)
class JobManager:
    """Very small in-memory queue / result store."""

    _running: set[str] = field(default_factory=set, init=False)
    _results: dict[str, str] = field(default_factory=dict, init=False)

    # ––––– public async helpers (FastAPI BackgroundTasks can await them) –––– #

    async def put(self, job_id: str, message: str) -> None:
        """Simulate a CPU-/IO-bound task that finishes after WAIT_SEC seconds."""
        self._running.add(job_id)
        logger.info("Started job {}", job_id)
        await asyncio.sleep(2.5)  # 👈 your real work happens here
        self._running.remove(job_id)
        self._results[job_id] = message
        logger.info("Job {} finished – saved result {!r}", job_id, message)

    # ––––– read helpers –––– #

    def has(self, job_id: str) -> bool:
        return job_id in self._running or job_id in self._results

    def is_ready(self, job_id: str) -> bool:
        return job_id in self._results

    def get(self, job_id: str) -> str:  # safe to call only if ready() is True
        return self._results[job_id]

    def all_done(self) -> ItemsView[str, str]:
        return self._results.items()


manager = JobManager()

# --------------------------------------------------------------------------- #
#  ROUTES
# --------------------------------------------------------------------------- #


@api.post(
    "/tasks",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Queue a new job and return its ID and URI.",
)
async def create_task(message: str, background: BackgroundTasks, response: Response) -> Job:
    if not message:
        raise HTTPException(status_code=400, detail="Message payload cannot be empty.")
    job = Job.new(endpoint_name="get_task")
    background.add_task(manager.put, job.id, message)
    # Expose canonical URL in a `Location` header (clients then do GET /tasks/{id}).
    response.headers["Location"] = job.uri
    return job


@api.get(
    "/tasks/{job_id}",
    name="get_task",  # url_path_for() uses this name (see Job.new)
    summary="Fetch the result of a job",
)
async def get_task(job_id: str) -> str | None:
    if not manager.has(job_id):
        raise HTTPException(status_code=404, detail="Job not found")
    if not manager.is_ready(job_id):
        # 202 Accepted → job exists but is still running; suggest retry delay
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail="Job still processing.  Retry later.",
            headers={"Retry-After": str(5)},
        )
    # All good – return the stored message (FastAPI will serialize a plain str)
    return manager.get(job_id)


@api.get("/tasks", summary="List all finished jobs.")
async def list_finished_tasks() -> dict[str, str]:
    return dict(manager.all_done())
