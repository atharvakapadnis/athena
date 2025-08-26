"""
Data validation and quality assurance for Smart Description Iterative Improvement System
"""
import pandas as pd
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Any
from .config import CLEANED_DATA_PATH, HTS_REFERENCE_PATH
from .logger import get_logger

logger = get_logger(__name__)

class DataValidator:
    """Validate data quality and integrity"""
    
    def __init__(self):
        self.hts_pattern = re.compile(r'^\d{4}\.\d{2}\.\d{2}\.\d{2}$')
    
    def validate_product_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate product data quality"""
        validation_results = {
            'total_products': len(df),
            'valid_hts_codes': 0,
            'missing_descriptions': 0,
            'duplicate_items': 0,
            'data_quality_score': 0.0,
            'issues': []
        }
        
        # Check HTS code format
        valid_hts = df['final_hts'].astype(str).str.match(self.hts_pattern)
        validation_results['valid_hts_codes'] = valid_hts.sum()
        
        # Check for missing descriptions
        missing_desc = df['item_description'].isna().sum()
        validation_results['missing_descriptions'] = missing_desc
        
        # Check for duplicates
        duplicates = df.duplicated(subset=['item_id']).sum()
        validation_results['duplicate_items'] = duplicates
        
        # Calculate quality score
        total_checks = len(df)
        passed_checks = validation_results['valid_hts_codes'] + (total_checks - missing_desc) + (total_checks - duplicates)
        validation_results['data_quality_score'] = passed_checks / (total_checks * 3)
        
        # Log issues
        if validation_results['valid_hts_codes'] < total_checks:
            validation_results['issues'].append(f"Invalid HTS codes: {total_checks - validation_results['valid_hts_codes']}")
        
        if missing_desc > 0:
            validation_results['issues'].append(f"Missing descriptions: {missing_desc}")
        
        if duplicates > 0:
            validation_results['issues'].append(f"Duplicate items: {duplicates}")
        
        return validation_results
    
    def validate_hts_reference(self, hts_data: List[Dict]) -> Dict[str, Any]:
        """Validate HTS reference data"""
        validation_results = {
            'total_codes': len(hts_data),
            'valid_hierarchy': True,
            'missing_descriptions': 0,
            'issues': []
        }
        
        # Check for missing descriptions
        missing_desc = sum(1 for item in hts_data if not item.get('description'))
        validation_results['missing_descriptions'] = missing_desc
        
        # Check hierarchy structure
        for item in hts_data:
            hts_code = item.get('htsno', '')
            if hts_code and not self.hts_pattern.match(hts_code):
                # Only check codes that look like full HTS codes (have dots)
                if '.' in hts_code and len(hts_code.split('.')) >= 4:
                    validation_results['valid_hierarchy'] = False
                    validation_results['issues'].append(f"Invalid HTS code format: {hts_code}")
        
        if missing_desc > 0:
            validation_results['issues'].append(f"Missing descriptions: {missing_desc}")
        
        return validation_results
    
    def get_data_summary(self, df: pd.DataFrame, hts_data: List[Dict]) -> Dict[str, Any]:
        """Get comprehensive data summary"""
        return {
            'products': {
                'total': len(df),
                'unique_hts_codes': df['final_hts'].nunique(),
                'material_classes': df['material_class'].value_counts().to_dict(),
                'product_groups': df['product_group'].value_counts().to_dict() if 'product_group' in df.columns else {}
            },
            'hts_reference': {
                'total_codes': len(hts_data),
                'chapters': list(set(item.get('htsno', '')[:4] for item in hts_data if item.get('htsno')))
            }
        }
