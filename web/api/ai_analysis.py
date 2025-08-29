from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, Any, Optional, List
import uuid
from datetime import datetime

from ..services.ai_service import AIService
from ..models.ai import (
    AnalysisRequest, AnalysisResponse, PatternAnalysisResponse,
    FeedbackRequest, FeedbackResponse, ConfidenceAnalysisResponse,
)
from ..models.common import APIResponse, PaginatedResponse
from ..middleware.auth import get_current_user
from ..models.user import User


router = APIRouter()

@router.post("/analyze-batch", response_model=APIResponse[AnalysisResponse])
async def analyze_batch(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    ai_service: AIService = Depends(),
):
    """ Trigger AI analysis for a batch """
    try:
        analysis = await ai_service.analyze_batch(
            batch_id=request.batch_id,
            analysis_types=request.analysis_types,
            user_id=user.username,
        )
        return APIResponse(
            status="success",
            data=analysis,
            message=f"AI analysis started for batch {request.batch_id}"
        )
    except Exception as e:
        return APIResponse(
            status="error",
            message=f"Failed to start analysis: {str(e)}",
        )

@router.get("/patterns", response_model=APIResponse[List[PatternAnalysisResponse]])
async def get_pattern_analysis(
    days: int = 30,
    pattern_type: Optional[str] = None,
    min_confidence: float = 0.6,
    user: User = Depends(get_current_user),
    ai_service: AIService = Depends()
):
    """ Get AI- identified patterns from recent batches """
    try:
        patterns = await ai_service.get_pattern_analysis(
            days=days,
            pattern_type=pattern_type,
            min_confidence=min_confidence,
        )
        return APIResponse(
            status="success",
            data=patterns,
            message=f"Retrieved {len(patterns)} patterns"
        )
    except Exception as e:
        return APIResponse(
            status="error",
            message=f"Failed to retrieve patterns: {str(e)}",
        )

@router.post("/confidence-analysis", response_model=APIResponse[ConfidenceAnalysisResponse])
async def get_confidence_analysis(
    batch_id: Optional[str] = None,
    days: int = 7,
    user: User = Depends(get_current_user),
    ai_service: AIService = Depends(),
):
    """ Get detaield confidence score analysis """
    try:
        analysis = await ai_service.get_confidence_analysis(
            batch_id=batch_id,
            days=days,
        )
        return APIResponse(
            status="success",
            data=analysis,
            message="Confidence analysis retrieved successfully",
        )
    except Exception as e:
        return APIResponse(
            status="error",
            message=f"Failed to retrieve confidence analysis: {str(e)}",
        )

@router.post("/feedback", response_model=APIResponse[FeedbackResponse])
async def submit_feedback(
    feedback: FeedbackRequest,
    user: User = Depends(get_current_user),
    ai_service: AIService = Depends(),
):
    """ Submit manual feedback for AI learning """
    try:
        result = await ai_service.submit_feedback(
            feedback=feedback,
            user_id=user.username,
        )
        return APIResponse(
            status="success",
            data=result,
            message="Feedback submitted successfully",
        )
    except Exception as e:
        return APIResponse(
            status="error",
            message=f"Failed to submit feedback: {str(e)}",
        )

@router.get("/suggestions", response_model=APIResponse[List[Dict]])
async def get_ai_suggestions(
    batch_id: Optional[str] = None,
    status: Optional[str] = None,
    confidence_threshold: float = 0.7,
    user: User = Depends(get_current_user),
    ai_service: AIService = Depends(),
):
    """ Get AI-suggestions for improvements """
    try:
        suggestions = await ai_service.get_ai_suggestions(
            batch_id=batch_id,
            status=status,
            confidence_threshold=confidence_threshold,
        )
        return APIResponse(
            status="success",
            data=suggestions,
            message=f"Retrieved {len(suggestions)} AI suggestions"
        )
    except Exception as e:
        return APIResponse(
            status="error",
            message=f"Failed to retrieve AI suggestions: {str(e)}",
        )

@router.get("/analysis-history", response_model=APIResponse[PaginatedResponse[Dict]])
async def get_analysis_history(
    page: int = 1,
    page_size: int = 20,
    analysis_type: Optional[str] = None,
    user: User = Depends(get_current_user),
    ai_service: AIService = Depends(),
):
    """ Get history of AI analysis """
    try:
        history = await ai_service.get_analysis_history(
            page=page,
            page_size=page_size,
            analysis_type=analysis_type,
        )
        return APIResponse(
            status="success",
            data=history,
            message="Analysis history retrieved successfully",
        )
    except Exception as e:
        return APIResponse(
            status="error",
            message=f"Failed to retrieve analysis history: {str(e)}",
        )