"""
Read-only endpoints consumed by the ops-facing Admin Dashboard
(loss ratios, manual review queue, claim analytics).
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/claims/review-queue")
async def get_manual_review_queue():
    raise NotImplementedError


@router.get("/analytics/loss-ratios")
async def get_loss_ratios():
    raise NotImplementedError
