"""
Data loading and validation utilities for Smart Description Iterative Improvement System
"""
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from .config import CLEANED_DATA_PATH, HTS_REFERENCE_PATH, ensure_directories

logger = logging.getLogger(__name__)

class DataLoader:
    """Handles loading and validation of HTS classification data"""
    
    def __init__(self):
        self.product_data: Optional[pd.DataFrame] = None
        self.hts_reference: Optional[List[Dict]] = None
        
        # Ensure directories exist
        ensure_directories()
    
    def load_product_data(self, file_path: Optional[Path] = None) -> pd.DataFrame:
        """
        Load and validate product data from CSV
        
        Args:
            file_path: Path to CSV file (defaults to cleaned data)
            
        Returns:
            DataFrame with product data
        """
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
            
            # Basic data validation
            df = self._validate_product_data(df)
            self.product_data = df
            
            return df
            
        except Exception as e:
            logger.error(f"Error loading product data: {e}")
            raise
    
    def load_hts_reference(self, file_path: Optional[Path] = None) -> List[Dict]:
        """
        Load HTS reference data from JSON
        
        Args:
            file_path: Path to JSON file (defaults to HTS reference)
            
        Returns:
            List of HTS code dictionaries
        """
        if file_path is None:
            file_path = HTS_REFERENCE_PATH
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                hts_data = json.load(f)
            
            logger.info(f"Loaded {len(hts_data)} HTS codes from {file_path}")
            
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
            if isinstance(item, dict):
                # Check for htsno field (actual data structure)
                if 'htsno' in item:
                    hts_code = str(item['htsno']).strip()
                    if hts_code and hts_code.count('.') >= 0:  # Allow any number of dots
                        validated_data.append(item)
                # Also check for hts_code field (alternative structure)
                elif 'hts_code' in item:
                    hts_code = str(item['hts_code']).strip()
                    if hts_code and hts_code.count('.') >= 0:
                        validated_data.append(item)
        
        logger.info(f"Validated HTS data: {len(validated_data)} valid codes")
        return validated_data
    
    def get_data_summary(self) -> Dict[str, any]:
        """Get summary statistics of loaded data"""
        if self.product_data is None or self.hts_reference is None:
            raise ValueError("Data not loaded. Call load_product_data() and load_hts_reference() first.")
        
        return {
            'products': {
                'total': len(self.product_data),
                'unique_hts_codes': self.product_data['final_hts'].nunique(),
                'material_classes': self.product_data['material_class'].value_counts().to_dict(),
                'product_groups': self.product_data.get('product_group', pd.Series()).value_counts().to_dict()
            },
            'hts_reference': {
                'total_codes': len(self.hts_reference),
                'chapters': list(set(code.get('htsno', code.get('hts_code', ''))[:4] for code in self.hts_reference if code.get('htsno') or code.get('hts_code')))
            }
        }
    
    def get_sample_products(self, n: int = 10) -> List[Dict]:
        """Get a sample of products for testing"""
        if self.product_data is None:
            raise ValueError("Product data not loaded. Call load_product_data() first.")
        
        sample_df = self.product_data.sample(n=min(n, len(self.product_data)))
        return sample_df.to_dict('records') 