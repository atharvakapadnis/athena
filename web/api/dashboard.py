from fastapi import APIRouter, Depends
from typing import Dict, Any, Optional

from ..services.dashboard_service import DashboardService
from ..models.dashboard import DashboardSummary

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