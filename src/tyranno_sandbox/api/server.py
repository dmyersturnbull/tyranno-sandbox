# SPDX-FileCopyrightText: Copyright 2020-2025, Contributors to Tyrannosaurus
# SPDX-PackageHomePage: https://github.com/dmyersturnbull/tyrannosaurus
# SPDX-License-Identifier: Apache-2.0
"""
Entrypoint for server.
"""

from pathlib import Path
from typing import Any

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


@api.get("/tasks/{task_id}")
async def get_object(task_id: str) -> dict[str, Any]:
    """
    Gets features for any particular user.
    """
    # return await ...


@api.post("/tasks/}")
async def post_data(payload: str, background_tasks: BackgroundTasks) -> dict[str, Any]:
    """
    On POST, submits the data to the ETL pipeline, then returns automatically.
    """
    logger.info("Received POST: '%s'", directory)
    # FastAPI is smart enough to know to execute this async (because etl() is declared async).
    background_tasks.add_task(etl, Path(directory))
    return {"message": f"Processing {directory}"}
