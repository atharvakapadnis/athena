"""
Data loading and validation utilities for Smart Description Iterative Improvement System
"""
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from .config import CLEANED_DATA_PATH, HTS_REFERENCE_PATH, ensure_directories
from .data_validator import DataValidator
from .logger import get_logger

logger = get_logger(__name__)

class DataLoader:
    """Enhanced data loader with validation"""
    
    def __init__(self):
        self.product_data: Optional[pd.DataFrame] = None
        self.hts_reference: Optional[List[Dict]] = None
        self.validator = DataValidator()
        
        # Ensure directories exist
        ensure_directories()
    
    def load_product_data(self, file_path: Optional[Path] = None, validate: bool = True) -> pd.DataFrame:
        """
        Load and validate product data from CSV
        
        Args:
            file_path: Path to CSV file (defaults to cleaned data)
            validate: Whether to perform data validation
            
        Returns:
            DataFrame with product data
        """
        if self.product_data is not None:
            return self.product_data
            
        if file_path is None:
            file_path = CLEANED_DATA_PATH
            
        try:
            df = pd.read_csv(file_path)
            logger.info(f"Loaded {len(df)} products from {file_path}")
            
            # Validate required columns
            required_columns = [
                'item_id', 'item_description', 'final_hts', 
                'material_class', 'material_detail'
            ]
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            if validate:
                validation_results = self.validator.validate_product_data(df)
                logger.info(f"Data validation results: {validation_results}")
                
                if validation_results['data_quality_score'] < 0.8:
                    logger.warning(f"Data quality score low: {validation_results['data_quality_score']}")
                    logger.warning(f"Issues: {validation_results['issues']}")
            
            # Basic data validation and filtering
            df = self._validate_product_data(df)
            self.product_data = df
            
            return df
            
        except Exception as e:
            logger.error(f"Error loading product data: {e}")
            raise
    
    def load_hts_reference(self, file_path: Optional[Path] = None, validate: bool = True) -> List[Dict]:
        """
        Load HTS reference data from JSON
        
        Args:
            file_path: Path to JSON file (defaults to HTS reference)
            validate: Whether to perform data validation
            
        Returns:
            List of HTS code dictionaries
        """
        if self.hts_reference is not None:
            return self.hts_reference
            
        if file_path is None:
            file_path = HTS_REFERENCE_PATH
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                hts_data = json.load(f)
            
            logger.info(f"Loaded {len(hts_data)} HTS codes from {file_path}")
            
            if validate:
                validation_results = self.validator.validate_hts_reference(hts_data)
                logger.info(f"HTS validation results: {validation_results}")
                
                if not validation_results['valid_hierarchy']:
                    logger.warning(f"HTS hierarchy issues: {validation_results['issues']}")
            
            # Validate HTS data structure
            hts_data = self._validate_hts_data(hts_data)
            self.hts_reference = hts_data
            
            return hts_data
            
        except Exception as e:
            logger.error(f"Error loading HTS reference data: {e}")
            raise
    
    def _validate_product_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate and clean product data"""
        original_count = len(df)
        
        # Remove rows with missing critical information
        df = df.dropna(subset=['item_id', 'item_description', 'final_hts'])
        
        # Ensure HTS codes are strings and properly formatted
        df['final_hts'] = df['final_hts'].astype(str).str.strip()
        
        # Remove invalid HTS codes (should be in format XXXX.XX.XX.XX)
        df = df[df['final_hts'].str.match(r'^\d{4}\.\d{2}\.\d{2}\.\d{2}$')]
        
        # Clean up item descriptions
        df['item_description'] = df['item_description'].astype(str).str.strip()
        
        # Remove empty descriptions
        df = df[df['item_description'].str.len() > 0]
        
        final_count = len(df)
        if final_count < original_count:
            logger.warning(f"Removed {original_count - final_count} invalid product records")
        
        logger.info(f"Validated product data: {final_count} records remaining")
        return df
    
    def _validate_hts_data(self, hts_data: List[Dict]) -> List[Dict]:
        """Validate HTS reference data structure"""
        validated_data = []
        
        for item in hts_data:
            if isinstance(item, dict) and item.get('htsno'):
                # Basic validation - item has required structure
                validated_data.append(item)
        
        logger.info(f"Validated HTS data: {len(validated_data)} valid codes")
        return validated_data
    
    def get_data_summary(self) -> Dict:
        """Get summary statistics of loaded data"""
        if self.product_data is None or self.hts_reference is None:
            raise ValueError("Data not loaded. Call load_product_data() and load_hts_reference() first.")
        
        return self.validator.get_data_summary(self.product_data, self.hts_reference)
    
    def get_sample_products(self, n: int = 10) -> List[Dict]:
        """Get a sample of products for testing"""
        if self.product_data is None:
            raise ValueError("Product data not loaded. Call load_product_data() first.")
        
        sample_df = self.product_data.sample(n=min(n, len(self.product_data)))
        return sample_df.to_dict('records') 