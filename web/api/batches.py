from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, Any, Optional, List
import uuid
from datetime import datetime

from ..services.batch_service import BatchService
from ..models.batch import(
    BatchConfigRequest, BatchResponse, BatchStatus,
    BatchHistoryResponse
)
from ..models.common import APIResponse, PaginatedResponse
from ..middleware.auth import get_mock_user as get_current_user
from ..models.user import User

router = APIRouter()

@router.post("/start", response_model=APIResponse[BatchResponse])
async def start_batch(
    config: BatchConfigRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    batch_service: BatchService = Depends(),
):
    """Start a new batch processing job"""
    try:
        batch = await batch_service.start_batch(config, user.username)

        # Add background task to monitor batch progress
        background_tasks.add_task(batch_service.monitor_batch, batch.batch_id)

        return APIResponse(
            status="success",
            data=batch,
            message=f"Batch {batch.batch_id} started successfully"
        )
    except Exception as e:
        return APIResponse(
            status="error",
            message=f"Failed to start batch: {str(e)}",
        )

@router.get("/queue", response_model=APIResponse[List[BatchResponse]])
async def get_batch_queue(
    user: User = Depends(get_current_user),
    batch_service: BatchService = Depends(),
):
    """Get the current batch queue"""
    try:
        queue = await batch_service.get_batch_queue()
        return APIResponse(
            status="success",
            data=queue,
            message="Batch queue retrieved successfully",
        )
    except Exception as e:
        return APIResponse(
            status="error",
            message=f"Failed to get batch queue: {str(e)}",
        )

@router.get("/history", response_model=APIResponse[PaginatedResponse[BatchHistoryResponse]])
async def get_batch_history(
    page: int = 1,
    page_size: int = 20,
    status: Optional[BatchStatus] = None,
    user: User = Depends(get_current_user),
    batch_service: BatchService = Depends(),
):
    """ Get batch processing history with pagination """
    try:
        history = await batch_service.get_batch_history(
            page=page,
            page_size=page_size,
            status_filter=status,
        )
        return APIResponse(
            status="success",
            data=history,
            message="Batch history retrieved successfully",
        )
    except Exception as e:
        return APIResponse(
            status="error",
            message=f"Failed to get batch history: {str(e)}",
        )

@router.get("/{batch_id}", response_model=APIResponse[BatchResponse])
async def get_batch_details(
    batch_id: str,
    user: User = Depends(get_current_user),
    batch_service: BatchService = Depends(),
):
    """ Get details of a specific batch """
    try:
        batch = await batch_service.get_batch_details(batch_id)
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")

        return APIResponse(
            status="success",
            data=batch,
            message="Batch details retrieved successfully",
        )
    except HTTPException:
        raise
    except Exception as e:
        return APIResponse(
            status="error",
            message=f"Failed to get batch details: {str(e)}",
        )

@router.get("/{batch_id}/results", response_model=APIResponse[Dict])
async def get_batch_results(
    batch_id: str,
    user: User = Depends(get_current_user),
    batch_service: BatchService = Depends(),
):
    """ Get enhanced AI processing results for a batch """
    try:
        results = await batch_service.get_batch_enhanced_results(batch_id)
        if not results:
            raise HTTPException(status_code=404, detail="Enhanced results not found")

        return APIResponse(
            status="success",
            data=results,
            message="Enhanced results retrieved successfully",
        )
    except HTTPException:
        raise
    except Exception as e:
        return APIResponse(
            status="error",
            message=f"Failed to get enhanced results: {str(e)}",
        )

# @router.get("/{batch_id}/complete", response_model=APIResponse[Dict])
# async def get_complete_batch_details(
#     batch_id: str,
#     user: User = Depends(get_current_user),
#     batch_service: BatchService = Depends(),
# ):
#     """ Get complete batch information including enhanced results """
#     try:
#         complete_info = await batch_service.get_batch_details_with_results(batch_id)
#         if not complete_info:
#             raise HTTPException(status_code=404, detail="Batch not found")
        
#         return APIResponse(
#             status="success",
#             data=complete_info,
#             message="Complete batch information retrieved successfully",
#         )
#     except HTTPException:
#         raise
#     except Exception as e:
#         return APIResponse(
#             status="error",
#             message=f"Failed to get complete batch info: {str(e)}",
#         )
        
@router.post("/{batch_id}/pause", response_model=APIResponse[Dict])
async def pause_batch(
    batch_id: str,
    user: User = Depends(get_current_user),
    batch_service: BatchService = Depends(),
):
    """ Pause a running batch """
    try:
        result = await batch_service.pause_batch(batch_id, user.username)
        return APIResponse(
            status="success",
            data=result,
            message=f"Batch {batch_id} paused successfully",
        )
    except Exception as e:
        return APIResponse(
            status="error",
            message=f"Failed to pause batch: {str(e)}",
        )

@router.post("/{batch_id}/resume", response_model=APIResponse[Dict])
async def resume_batch(
    batch_id: str,
    user: User = Depends(get_current_user),
    batch_service: BatchService = Depends(),
):
    """ Resume a paused batch """
    try:
        result = await batch_service.resume_batch(batch_id, user.username)
        return APIResponse(
            status="success",
            data=result,
            message=f"Batch {batch_id} resumed successfully",
        )
    except Exception as e:
        return APIResponse(
            status="error",
            message=f"Failed to resume batch: {str(e)}",
        )

@router.post("/{batch_id}/cancel", response_model=APIResponse[Dict])
async def cancel_batch(
    batch_id: str,
    reason: Optional[str] = None,
    user: User = Depends(get_current_user),
    batch_service: BatchService = Depends(),
):
    """ Cancel a batch """
    try:
        result = await batch_service.cancel_batch(batch_id, user.username, reason)
        return APIResponse(
            status="success",
            data=result,
            message=f"Batch {batch_id} cancelled successfully",
        )
    except Exception as e:
        return APIResponse(
            status="error",
            message=f"Failed to cancel batch: {str(e)}",
        )

# Dynamic scaling endpoints
# @router.get("/scaling/status", response_model=APIResponse[Dict])
# async def get_scaling_status(
#     user: User = Depends(get_current_user),
#     batch_service: BatchService = Depends(),
# ):
#     """ Get dynamic scaling status"""
#     try:
#         status = await batch_service.get_scaling_status()
#         return APIResponse(
#             status="success",
#             data=status,
#             message="Scaling status retrieved successfully",
#         )
#     except Exception as e:
#         return APIResponse(
#             status="error",
#             message=f"Failed to get scaling status: {str(e)}",
#         )

# @router.post("/scaling/configure", response_model=APIResponse[Dict])
# async def configure_scaling(
#     config: ScalingConfigRequest,
#     user: User = Depends(get_current_user),
#     batch_service: BatchService = Depends(),
# ):
#     """ Configure dynamic scaling parameters"""
#     try:
#         result = await batch_service.configure_scaling(config, user.username)
#         return APIResponse(
#             status="success",
#             data=result,
#             message="Scaling configuration updated successfully",
#         )
#     except Exception as e:
#         return APIResponse(
#             status="error",
#             message=f"Failed to configure scaling: {str(e)}",
#         )

# @router.post("/scaling/enable", response_model=APIResponse[Dict])
# async def enable_scaling(
#     user: User = Depends(get_current_user),
#     batch_service: BatchService = Depends(),
# ):
#     """ Enable dynamic scaling"""
#     try:
#         result = await batch_service.enable_scaling(user.username)
#         return APIResponse(
#             status="success",
#             data=result,
#             message=" Dynamic caling enabled successfully",
#         )
#     except Exception as e:
#         return APIResponse(
#             status="error",
#             message=f"Failed to enable scaling: {str(e)}",
#         )

# @router.post("/scaling/disable", response_model=APIResponse[Dict])
# async def disable_scaling(
#     user: User = Depends(get_current_user),
#     batch_service: BatchService = Depends(),
# ):
#     """ Disable dynamic scaling """
#     try:
#         result = await batch_service.disable_scaling(user.username)
#         return APIResponse(
#             status="success",
#             data=result,
#             message="Dynamic scaling disabled successfully"
#         )
#     except Exception as e:
#         return APIResponse(
#             status="error",
#             message=f"Failed to disable scaling: {str(e)}",
#         )