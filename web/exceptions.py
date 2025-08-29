from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
import traceback
from typing import Union

logger = logging.getLogger(__name__)

class AthenaException(Exception):
    """Base exception for Athena system"""
    def __init__(self, message: str, error_code: str = "ATHENA_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class BatchProcessingError(AthenaException):
    """Exception for batch processing errors"""
    def __init__(self, message: str, batch_id: str = None):
        self.batch_id = batch_id
        super().__init__(message, "BATCH_ERROR")

class RuleManagementError(AthenaException):
    """Exception for rule management errors"""
    def __init__(self, message: str, rule_id: str = None):
        self.rule_id = rule_id
        super().__init__(message, "RULE_ERROR")

class AIAnalysisError(AthenaException):
    """Exception for AI analysis errors"""
    def __init__(self, message: str, analysis_type: str = None):
        self.analysis_type = analysis_type
        super().__init__(message, "AI_ERROR")

def setup_exception_handlers(app: FastAPI):
    """Setup comprehensive exception handlers for internal deployment"""
    
    @app.exception_handler(AthenaException)
    async def athena_exception_handler(request: Request, exc: AthenaException):
        """Handle custom Athena exceptions"""
        logger.error(f"Athena Error: {exc.message}", extra={
            'error_code': exc.error_code,
            'path': request.url.path,
            'method': request.method
        })
        
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": exc.message,
                "error_code": exc.error_code,
                "timestamp": str(traceback.format_exc()),
                "request_id": getattr(request.state, 'request_id', None)
            }
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions with detailed logging for internal use"""
        logger.warning(f"HTTP Error {exc.status_code}: {exc.detail}", extra={
            'path': request.url.path,
            'method': request.method,
            'status_code': exc.status_code
        })
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "message": exc.detail,
                "status_code": exc.status_code,
                "timestamp": str(traceback.format_exc()),
                "path": request.url.path
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle request validation errors with detailed info for internal debugging"""
        logger.error(f"Validation Error: {exc.errors()}", extra={
            'path': request.url.path,
            'method': request.method,
            'body': await request.body() if hasattr(request, 'body') else None
        })
        
        return JSONResponse(
            status_code=422,
            content={
                "status": "error",
                "message": "Request validation failed",
                "details": exc.errors(),
                "timestamp": str(traceback.format_exc())
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle all other exceptions with full details for internal network"""
        logger.error(f"Unhandled Exception: {str(exc)}", extra={
            'path': request.url.path,
            'method': request.method,
            'exception_type': type(exc).__name__,
            'traceback': traceback.format_exc()
        })
        
        # For internal deployment, include full traceback for debugging
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Internal server error: {str(exc)}",
                "exception_type": type(exc).__name__,
                "traceback": traceback.format_exc(),  # Safe for internal network
                "timestamp": str(traceback.format_exc())
            }
        )