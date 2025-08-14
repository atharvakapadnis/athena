#!/usr/bin/env python3
"""
Setup validation script for Smart Description Iterative Improvement System
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.config import validate_environment, get_project_settings, ensure_directories
from utils.data_loader import DataLoader
from utils.logger import setup_logging, get_logger

def main():
    """Run setup validation"""
    print("🔧 Smart Description Iterative Improvement System - Setup Validation")
    print("=" * 70)
    
    # Step 1: Validate environment
    print("\n1. Validating environment...")
    try:
        validate_environment()
        print("   ✅ Environment validation passed")
    except Exception as e:
        print(f"   ❌ Environment validation failed: {e}")
        return False
    
    # Step 2: Check project settings
    print("\n2. Checking project settings...")
    try:
        settings = get_project_settings()
        print(f"   ✅ Project settings loaded: {len(settings)} settings")
        print(f"   📁 Project root: {settings['project_root']}")
        print(f"   📊 Batch size: {settings['batch_size']}")
    except Exception as e:
        print(f"   ❌ Project settings failed: {e}")
        return False
    
    # Step 3: Ensure directories
    print("\n3. Creating directories...")
    try:
        ensure_directories()
        print("   ✅ Directories created successfully")
    except Exception as e:
        print(f"   ❌ Directory creation failed: {e}")
        return False
    
    # Step 4: Setup logging
    print("\n4. Setting up logging...")
    try:
        setup_logging()
        logger = get_logger("setup_validation")
        logger.info("Setup validation started")
        print("   ✅ Logging setup successful")
    except Exception as e:
        print(f"   ❌ Logging setup failed: {e}")
        return False
    
    # Step 5: Test data loading
    print("\n5. Testing data loading...")
    try:
        loader = DataLoader()
        
        # Load product data
        df = loader.load_product_data()
        print(f"   ✅ Product data loaded: {len(df)} products")
        
        # Load HTS reference
        hts_data = loader.load_hts_reference()
        print(f"   ✅ HTS reference loaded: {len(hts_data)} codes")
        
        # Get data summary
        summary = loader.get_data_summary()
        print(f"   ✅ Data summary generated")
        print(f"      - Unique HTS codes: {summary['products']['unique_hts_codes']}")
        print(f"      - Material classes: {len(summary['products']['material_classes'])}")
        
    except Exception as e:
        print(f"   ❌ Data loading failed: {e}")
        return False
    
    # Step 6: Test sample data
    print("\n6. Testing sample data retrieval...")
    try:
        sample = loader.get_sample_products(n=3)
        print(f"   ✅ Sample data retrieved: {len(sample)} items")
        
        # Show sample
        for i, item in enumerate(sample):
            print(f"      Sample {i+1}: {item.get('item_id', 'N/A')} - {item.get('item_description', 'N/A')[:50]}...")
            
    except Exception as e:
        print(f"   ❌ Sample data retrieval failed: {e}")
        return False
    
    # Step 7: Test imports
    print("\n7. Testing module imports...")
    try:
        from utils.debug import save_debug_data, analyze_batch_results
        from utils.smart_description_generator import SmartDescriptionGenerator
        from utils.hts_hierarchy import HTSHierarchy
        print("   ✅ All module imports successful")
    except Exception as e:
        print(f"   ❌ Module imports failed: {e}")
        return False
    
    print("\n" + "=" * 70)
    print("🎉 Setup validation completed successfully!")
    print("✅ All components are ready for the iterative improvement system")
    print("\nNext steps:")
    print("1. Proceed to [02_DATA_INTEGRATION.md] for data integration")
    print("2. Implement [03_BATCH_PROCESSOR.md] for batch processing")
    print("3. Run tests: python -m pytest tests/test_project_setup.py -v")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
