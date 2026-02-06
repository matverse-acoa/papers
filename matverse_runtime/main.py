from __future__ import annotations

from fastapi import FastAPI

from matverse_runtime.loop_endpoint import router as loop_router
from matverse_runtime.publish_endpoint import router as publish_router

app = FastAPI(title="MatVerse Runtime API")
app.include_router(publish_router, prefix="/publish")

app.include_router(loop_router, prefix="/loop")
