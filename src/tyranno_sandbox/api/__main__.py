import asyncio

from hypercorn.asyncio import serve
from hypercorn.config import Config

from tyranno_sandbox.api.server import api

asyncio.run(serve(api, Config()))
