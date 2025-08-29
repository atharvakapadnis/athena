from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, Any, Optional, List
import uuid
from datetime import datetime

from ..services.rule_service import RuleService
from ..models.rule import(
    RuleRequest, RuleResponse, RuleDecisionRequest,
    RuleSuggestionResponse, RulePerformanceResponse
)
from ..models.common import APIResponse, PaginatedResponse

from ..middleware.auth import get_current_user
from ..models.user import User

router = APIRouter()

@router.get("/suggestions", response_model=APIResponse[List[RuleSuggestionResponse]])
async def get_pending_suggestions(
    priority_threshold: Optional[int] = None,
    confidence_threshold: Optional[float] = None,
    user: User = Depends(get_current_user),
    rule_service: RuleService = Depends(),
):
    """Get pending rules suggestions for review"""
    try:
        suggestions = await rule_service.get_pending_suggestions(
            priority_threshold=priority_threshold,
            confidence_threshold=confidence_threshold,
        )
        return APIResponse(
            status="success",
            data=suggestions,
            message=f"Retrieved {len(suggestions)} pending suggestions",
        )
    except Exception as e:
        return APIResponse(
            status="error",
            message=f"Failed to retrieve suggestions: {str(e)}",
        )

@router.post("/suggestions/{suggestion_id}/decision", response_model=APIResponse[Dict])
async def make_rule_decision(
    suggestion_id: str,
    decision: RuleDecisionRequest,
    user: User = Depends(get_current_user),
    rule_service: RuleService = Depends(),
):
    """" Make a decision on a rule suggestion (approve /reject/ modify)"""
    try:
        result = await rule_service.make_rule_decision(
            suggestion_id=suggestion_id,
            decision=decision,
            user=user.username
        )
        
        action = "approved" if decision.decision == "approve" else "rejected"
        return APIResponse(
            status="success",
            data=result,
            message=f"Rule suggestion {action} successfully",
        )
    except Exception as e:
        return APIResponse(
            status="error",
            message=f"Failed to make decision: {str(e)}",
        )

@router.get("/active", response_model=APIResponse[List[RuleResponse]])
async def get_active_rules(
    rule_type: Optional[str] = None,
    user: User = Depends(get_current_user),
    rule_service: RuleService = Depends(),
):
    """Get all active rules"""
    try:
        rules = await rule_service.get_active_rules(rule_type=rule_type)
        return APIResponse(
            status="success",
            data=rules,
            message=f"Retrieved {len(rules)} active rules",
        )
    except Exception as e:
        return APIResponse(
            status="error",
            message=f"Failed to retrieve active rules: {str(e)}",
        )

@router.get("/create", response_model=APIResponse[RuleResponse])
async def create_manual_rule(
    rule: RuleRequest,
    user: User = Depends(get_current_user),
    rule_service: RuleService = Depends(),
):
    """Create a new rule manually"""
    try:
        new_rule = await rule_service.create_manual_rule(
            rule=rule,
            creator=user.username,
        )
        return APIResponse(
            status="success",
            data=new_rule,
            message="Rule created successfully",
        )
    except Exception as e:
        return APIResponse(
            status="error",
            message=f"Failed to create rule: {str(e)}",
        )

@router.get("/{rule_id}/performance", response_model=APIResponse[RulePerformanceResponse])
async def get_rule_performance(
    rule_id: str,
    days: int = 30,
    user: User = Depends(get_current_user),
    rule_service: RuleService = Depends()
):
    """Get performance metrics for a specific rule"""
    try:
        performance = await rule_service.get_rule_performance(
            rule_id=rule_id,
            days=days
        )
        return APIResponse(
            status="success",
            data=performance,
            message="Rule performance retrieved successfully"
        )
    except Exception as e:
        return APIResponse(
            status="error",
            message=f"Failed to retrieve rule performance: {str(e)}"
        )

@router.put("/{rule_id}", response_model=APIResponse[RuleResponse])
async def update_rule(
    rule_id: str,
    rule: RuleRequest,
    user: User = Depends(get_current_user),
    rule_service: RuleService = Depends()
):
    """Update an existing rule"""
    try:
        updated_rule = await rule_service.update_rule(
            rule_id=rule_id,
            rule=rule,
            modifier=user.username
        )
        return APIResponse(
            status="success",
            data=updated_rule,
            message="Rule updated successfully"
        )
    except Exception as e:
        return APIResponse(
            status="error",
            message=f"Failed to update rule: {str(e)}"
        )

@router.delete("/{rule_id}", response_model=APIResponse[Dict])
async def deactivate_rule(
    rule_id: str,
    reason: Optional[str] = None,
    user: User = Depends(get_current_user),
    rule_service: RuleService = Depends()
):
    """Deactivate a rule"""
    try:
        result = await rule_service.deactivate_rule(
            rule_id=rule_id,
            reason=reason,
            deactivator=user.username
        )
        return APIResponse(
            status="success",
            data=result,
            message="Rule deactivated successfully"
        )
    except Exception as e:
        return APIResponse(
            status="error",
            message=f"Failed to deactivate rule: {str(e)}"
        )

@router.get("/{rule_id}/history", response_model=APIResponse[List[Dict]])
async def get_rule_history(
    rule_id: str,
    user: User = Depends(get_current_user),
    rule_service: RuleService = Depends()
):
    """Get version history for a rule"""
    try:
        history = await rule_service.get_rule_history(rule_id)
        return APIResponse(
            status="success",
            data=history,
            message="Rule history retrieved successfully"
        )
    except Exception as e:
        return APIResponse(
            status="error",
            message=f"Failed to retrieve rule history: {str(e)}"
        )

@router.post("/bulk-action", response_model=APIResponse[Dict])
async def perform_bulk_action(
    rule_ids: List[str],
    action: str,  # activate, deactivate, delete
    reason: Optional[str] = None,
    user: User = Depends(get_current_user),
    rule_service: RuleService = Depends()
):
    """Perform bulk action on multiple rules"""
    try:
        result = await rule_service.perform_bulk_action(
            rule_ids=rule_ids,
            action=action,
            reason=reason,
            user=user.username
        )
        return APIResponse(
            status="success",
            data=result,
            message=f"Bulk action '{action}' completed successfully"
        )
    except Exception as e:
        return APIResponse(
            status="error",
            message=f"Failed to perform bulk action: {str(e)}"
        )