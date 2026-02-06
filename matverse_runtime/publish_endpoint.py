from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from matverse_fortified_publisher import run_fortified_publish
from matverse_runtime.pbse import validate_tx_id

router = APIRouter()


class PublishRequest(BaseModel):
    tx_id: str
    metadata: dict
    files: list[str]


@router.post("/fortified")
def publish_fortified(req: PublishRequest) -> dict[str, str]:
    if not validate_tx_id(req.tx_id):
        raise HTTPException(status_code=403, detail="PBSE tx_id inválido ou não aprovado")

    result = run_fortified_publish(
        tx_id=req.tx_id,
        metadata=req.metadata,
        files=req.files,
    )

    return {
        "doi": result["doi"],
        "ipfs": result["ipfs"],
        "evidence_hash": result["evidence_hash"],
        "repo_commit": result["commit"],
    }
