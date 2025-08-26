"""
Configuration settings for Smart Description Iterative Improvement System
"""
import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent  # Go up to project root
DATA_DIR = PROJECT_ROOT / "data"
INPUT_DIR = DATA_DIR / "input"
BATCHES_DIR = DATA_DIR / "batches"
RULES_DIR = DATA_DIR / "rules"
LOGS_DIR = DATA_DIR / "logs"
METRICS_DIR = DATA_DIR / "metrics"

# Data files
CLEANED_DATA_PATH = INPUT_DIR / "cleaned_test_ch73.csv"
HTS_REFERENCE_PATH = INPUT_DIR / "htsdata_ch73.json"

# Batch processing settings
DEFAULT_BATCH_SIZE = 50
CONFIDENCE_THRESHOLD_HIGH = 0.8
CONFIDENCE_THRESHOLD_MEDIUM = 0.6
CONFIDENCE_THRESHOLD_LOW = 0.4

# AI settings
OPENAI_MODEL = "gpt-4"
OPENAI_MAX_TOKENS = 2000
OPENAI_TEMPERATURE = 0.3

# Rule management settings
RULE_VERSIONING_ENABLED = True
AUTO_BACKUP_ENABLED = True
MAX_RULE_VERSIONS = 10

# Logging settings
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# HTS hierarchy levels
HTS_LEVELS = {
    0: "heading",      # 4-digit (e.g., 7301)
    1: "subheading",   # 6-digit (e.g., 7301.10)
    2: "statistical",  # 8-digit (e.g., 7301.10.00)
    3: "tariff"        # 10-digit (e.g., 7301.10.00.00)
}

# Environment variables
def get_openai_api_key() -> str:
    """Get OpenAI API key from environment variables"""
    return os.getenv("OPENAI_API_KEY", "")

def get_project_settings() -> Dict[str, Any]:
    """Get all project settings as a dictionary"""
    return {
        'project_root': str(PROJECT_ROOT),
        'data_dir': str(DATA_DIR),
        'input_dir': str(INPUT_DIR),
        'batches_dir': str(BATCHES_DIR),
        'rules_dir': str(RULES_DIR),
        'logs_dir': str(LOGS_DIR),
        'metrics_dir': str(METRICS_DIR),
        'batch_size': DEFAULT_BATCH_SIZE,
        'confidence_threshold_high': CONFIDENCE_THRESHOLD_HIGH,
        'confidence_threshold_medium': CONFIDENCE_THRESHOLD_MEDIUM,
        'confidence_threshold_low': CONFIDENCE_THRESHOLD_LOW,
        'openai_model': OPENAI_MODEL,
        'openai_max_tokens': OPENAI_MAX_TOKENS,
        'openai_temperature': OPENAI_TEMPERATURE,
        'rule_versioning_enabled': RULE_VERSIONING_ENABLED,
        'auto_backup_enabled': AUTO_BACKUP_ENABLED,
        'log_level': LOG_LEVEL
    }

def ensure_directories():
    """Create necessary directories if they don't exist"""
    directories = [
        INPUT_DIR, BATCHES_DIR, RULES_DIR, LOGS_DIR, METRICS_DIR,
        RULES_DIR / "rule_versions"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Ensured directory exists: {directory}")

def validate_environment():
    """Validate that the environment is properly configured"""
    errors = []
    
    # Check OpenAI API key
    if not get_openai_api_key():
        errors.append("OPENAI_API_KEY not found in environment variables")
    
    # Check data files exist
    if not CLEANED_DATA_PATH.exists():
        errors.append(f"Product data file not found: {CLEANED_DATA_PATH}")
    
    if not HTS_REFERENCE_PATH.exists():
        errors.append(f"HTS reference file not found: {HTS_REFERENCE_PATH}")
    
    # Check directories
    try:
        ensure_directories()
    except Exception as e:
        errors.append(f"Failed to create directories: {e}")
    
    if errors:
        raise ValueError(f"Environment validation failed:\n" + "\n".join(errors))
    
    print("Environment validation passed")
    return True 