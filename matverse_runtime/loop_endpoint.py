from __future__ import annotations

import json
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field
from starlette.responses import StreamingResponse

from matverse_runtime.loop_controller import loop_controller

router = APIRouter()


class AccelerateRequest(BaseModel):
    factor: int = Field(ge=1)


class TriggerRequest(BaseModel):
    type: Literal["doi", "cron", "manual"]
    tx_id: str | None = None
    doi: str | None = None


@router.get("/status")
def loop_status() -> dict:
    return loop_controller.status()


@router.get("/audit")
def loop_audit(limit: int = 100) -> list[dict]:
    return loop_controller.audit(limit=limit)


@router.post("/pause")
def loop_pause() -> dict:
    return loop_controller.pause()


@router.post("/start")
def loop_start() -> dict:
    return loop_controller.start()


@router.post("/accelerate")
def loop_accelerate(req: AccelerateRequest) -> dict:
    return loop_controller.accelerate(req.factor)


@router.post("/destroy")
def loop_destroy() -> dict:
    return loop_controller.destroy()


@router.post("/trigger")
def loop_trigger(req: TriggerRequest) -> dict:
    return loop_controller.trigger(trigger_type=req.type, tx_id=req.tx_id, doi=req.doi)


@router.get("/stream")
def loop_stream() -> StreamingResponse:
    def event_stream():
        while True:
            event = loop_controller.stream_next()
            if event is None:
                yield ": keepalive\n\n"
            else:
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
