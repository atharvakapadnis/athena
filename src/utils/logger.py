"""
Logging utilities for Smart Description Iterative Improvement System
"""
import structlog
import logging
from pathlib import Path
from typing import Optional
from .config import LOGS_DIR, LOG_LEVEL, LOG_FORMAT

def setup_logging(log_level: str = LOG_LEVEL, log_file: Optional[str] = None):
    """Setup structured logging for the system"""
    
    # Create logs directory if it doesn't exist
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Set default log file if not specified
    if log_file is None:
        log_file = LOGS_DIR / "system.log"
    
    # Configure structlog processors
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ]
    
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Setup file logging
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(getattr(logging, log_level.upper()))
    
    # Setup console logging
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper()))
    
    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT)
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    print(f"Logging configured: {log_level} level, file: {log_file}")

def get_logger(name: str):
    """Get a structured logger for the given name"""
    return structlog.get_logger(name)

def log_batch_processing(batch_id: str, total_items: int, successful_items: int, 
                        failed_items: int, processing_time: float, confidence_distribution: dict):
    """Log batch processing results"""
    logger = get_logger("batch_processor")
    
    logger.info("Batch processing completed",
                batch_id=batch_id,
                total_items=total_items,
                successful_items=successful_items,
                failed_items=failed_items,
                processing_time=processing_time,
                confidence_distribution=confidence_distribution,
                success_rate=successful_items/total_items if total_items > 0 else 0)

def log_ai_analysis(batch_id: str, analysis_type: str, tokens_used: int, 
                   suggestions_count: int, confidence: float):
    """Log AI analysis results"""
    logger = get_logger("ai_analysis")
    
    logger.info("AI analysis completed",
                batch_id=batch_id,
                analysis_type=analysis_type,
                tokens_used=tokens_used,
                suggestions_count=suggestions_count,
                confidence=confidence)

def log_rule_changes(rule_name: str, change_type: str, user: str, 
                    old_value: Optional[str] = None, new_value: Optional[str] = None):
    """Log rule changes for audit trail"""
    logger = get_logger("rule_editor")
    
    logger.info("Rule change applied",
                rule_name=rule_name,
                change_type=change_type,
                user=user,
                old_value=old_value,
                new_value=new_value)

def log_system_event(event_type: str, description: str, **kwargs):
    """Log general system events"""
    logger = get_logger("system")
    
    logger.info("System event",
                event_type=event_type,
                description=description,
                **kwargs)
