from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, Optional, List
import psutil
import os
from datetime import datetime
from pathlib import Path

from ..services.system_service import SystemService
from ..models.system import (
    SystemHealthResponse, ConfigurationRequest, ConfigurationResponse,
    UserRequest, UserResponse, SystemStatsResponse, MaintenanceRequest
)
from ..models.common import APIResponse
from ..middleware.auth import get_current_user
from ..models.user import User

router = APIRouter()

@router.get("/health", response_model=APIResponse[SystemHealthResponse])
async def get_system_health(
    user: User = Depends(get_current_user),
    system_service: SystemService = Depends()
):
    """Get comprehensive system health information"""
    try:
        health = await system_service.get_system_health()
        return APIResponse(
            status="success",
            data=health,
            message="System health retrieved successfully"
        )
    except Exception as e:
        return APIResponse(
            status="error",
            message=f"Failed to retrieve system health: {str(e)}"
        )

@router.get("/stats", response_model=APIResponse[SystemStatsResponse])
async def get_system_stats(
    user: User = Depends(get_current_user),
    system_service: SystemService = Depends()
):
    """Get detailed system statistics"""
    try:
        stats = await system_service.get_system_stats()
        return APIResponse(
            status="success",
            data=stats,
            message="System statistics retrieved successfully"
        )
    except Exception as e:
        return APIResponse(
            status="error",
            message=f"Failed to retrieve system statistics: {str(e)}"
        )

@router.get("/configuration", response_model=APIResponse[Dict])
async def get_system_configuration(
    user: User = Depends(get_current_user),
    system_service: SystemService = Depends()
):
    """Get current system configuration"""
    try:
        config = await system_service.get_configuration()
        return APIResponse(
            status="success",
            data=config,
            message="System configuration retrieved successfully"
        )
    except Exception as e:
        return APIResponse(
            status="error",
            message=f"Failed to retrieve configuration: {str(e)}"
        )

@router.post("/configuration", response_model=APIResponse[Dict])
async def update_system_configuration(
    config: ConfigurationRequest,
    user: User = Depends(get_current_user),
    system_service: SystemService = Depends()
):
    """Update system configuration"""
    try:
        result = await system_service.update_configuration(config, user.username)
        return APIResponse(
            status="success",
            data=result,
            message="System configuration updated successfully"
        )
    except Exception as e:
        return APIResponse(
            status="error",
            message=f"Failed to update configuration: {str(e)}"
        )

@router.post("/maintenance", response_model=APIResponse[Dict])
async def perform_maintenance(
    maintenance: MaintenanceRequest,
    user: User = Depends(get_current_user),
    system_service: SystemService = Depends()
):
    """Perform system maintenance tasks"""
    try:
        result = await system_service.perform_maintenance(maintenance, user.username)
        return APIResponse(
            status="success",
            data=result,
            message=f"Maintenance task '{maintenance.task_type}' completed successfully"
        )
    except Exception as e:
        return APIResponse(
            status="error",
            message=f"Failed to perform maintenance: {str(e)}"
        )

@router.get("/logs", response_model=APIResponse[List[Dict]])
async def get_system_logs(
    level: Optional[str] = None,
    component: Optional[str] = None,
    limit: int = 100,
    user: User = Depends(get_current_user),
    system_service: SystemService = Depends()
):
    """Get system logs"""
    try:
        logs = await system_service.get_logs(
            level=level,
            component=component,
            limit=limit
        )
        return APIResponse(
            status="success",
            data=logs,
            message=f"Retrieved {len(logs)} log entries"
        )
    except Exception as e:
        return APIResponse(
            status="error",
            message=f"Failed to retrieve logs: {str(e)}"
        )

@router.post("/backup", response_model=APIResponse[Dict])
async def create_backup(
    backup_type: str = "full",
    user: User = Depends(get_current_user),
    system_service: SystemService = Depends()
):
    """Create system backup"""
    try:
        result = await system_service.create_backup(backup_type, user.username)
        return APIResponse(
            status="success",
            data=result,
            message="Backup created successfully"
        )
    except Exception as e:
        return APIResponse(
            status="error",
            message=f"Failed to create backup: {str(e)}"
        )

@router.get("/users", response_model=APIResponse[List[UserResponse]])
async def get_users(
    user: User = Depends(get_current_user),
    system_service: SystemService = Depends()
):
    """Get all system users (basic implementation)"""
    try:
        users = await system_service.get_users()
        return APIResponse(
            status="success",
            data=users,
            message=f"Retrieved {len(users)} users"
        )
    except Exception as e:
        return APIResponse(
            status="error",
            message=f"Failed to retrieve users: {str(e)}"
        )

@router.post("/users", response_model=APIResponse[UserResponse])
async def create_user(
    new_user: UserRequest,
    user: User = Depends(get_current_user),
    system_service: SystemService = Depends()
):
    """Create a new user (basic implementation)"""
    try:
        created_user = await system_service.create_user(new_user, user.username)
        return APIResponse(
            status="success",
            data=created_user,
            message="User created successfully"
        )
    except Exception as e:
        return APIResponse(
            status="error",
            message=f"Failed to create user: {str(e)}"
        )