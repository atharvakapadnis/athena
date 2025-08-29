from fastapi import APIRouter, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import Dict, Any, Optional
import asyncio
import json

from ..services.dashboard_service import DashboardService
from ..models.dashboard import (
    DashboardSummary, ExecutiveSummary, RealTimeMetrics, PerformanceMetrics, QualityMetrics
)

from ..models.common import APIResponse
from ..middleware.auth import get_current_user
from ..models.user import User

router = APIRouter()

@router.get("/summary", response_model = APIResponse[DashboardSummary])
async def get_dashboard_summary(
    user: User = Depends(get_current_user),
    dashboard_service: DashboardService = Depends()
):
    """ Get comprehensive dashboard summary """
    try:
        summary = await dashboard_service.get_dashboard_summary()
        return APIResponse(
            status = "success",
            data = summary,
            message = "Dashboard summary fetched successfully"
        )
    except Exception as e:
        return APIResponse(
            status = "error",
            message = f"Failed to fetch dashboard summary: {str(e)}",
        )

@router.get("/real-time", response_model = APIResponse[RealTimeMetrics])
async def get_real_time_metrics(
    user: User = Depends(get_current_user),
    dashboard_services: DashboardService = Depends()
):
    """ Get real-time metrics """
    try:
        metrics = await dashboard_services.get_real_time_metrics()
        return APIResponse(
            status = "success",
            data = metrics,
            message = "Real-time metrics fetched successfully"
        )
    except Exception as e:
        return APIResponse(
            status = "error",
            message = f"Failed to fetch real-time metrics: {str(e)}",
        )

@router.get("/executive", response_model = APIResponse[ExecutiveSummary])
async def get_executive_summary(
    user: User = Depends(get_current_user),
    dashboard_services: DashboardService = Depends()
):
    """ Get executive summary """
    try:
        summary = await dashboard_services.get_executive_summary()
        return APIResponse(
            status = "success",
            data = summary,
            message = "Executive summary fetched successfully"
        )
    except Exception as e:
        return APIResponse(
            status = "error",
            message = f"Failed to fetch executive summary: {str(e)}",
        )

@router.get("/performance-history")
async def get_performance_history(
    days: int = 30,
    user: User = Depends(get_current_user),
    dashboard_services: DashboardService = Depends()
):
    """ Get performance history """
    try:
        history = await dashboard_services.get_performance_history(days)
        return APIResponse(
            status = "success",
            data = history,
            message = f"Performance history for {days} days fetched successfully"
        )
    except Exception as e:
        return APIResponse(
            status = "error",
            message = f"Failed to fetch performance history: {str(e)}",
        )

@router.get("/stream")
async def stream_dashboard_updates(
    user: User = Depends(get_current_user),
    dashboard_services: DashboardService = Depends()
):
    """ Stream dashboard updates """
    async def event_generator():
        while True:
            try:
                # Get latest metrics
                metrics = await dashboard_services.get_real_time_metrics()

                # Format as SSE
                event_data = json.dumps(metrics.dict())
                yield f"data: {event_data}\n\n"

                # Wait before next update
                await asyncio.sleep(5)
            except Exception as e:
                yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
                await asyncio.sleep(10) # Longer wait on error

    return StreamingResponse(
        event_generator(),
        media_type = "text/plain",
        headers = {"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )