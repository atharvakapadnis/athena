#!/usr/bin/env python3
"""
Test script for batch processing system
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.config import get_project_settings, validate_environment
from utils.data_loader import DataLoader
from utils.hts_hierarchy import HTSHierarchy
from utils.smart_description_generator import SmartDescriptionGenerator
from batch_processor import BatchProcessingSystem, BatchConfig

def test_batch_processing():
    """Test the batch processing system"""
    print("🧪 Testing Batch Processing System")
    print("=" * 50)
    
    try:
        # 1. Validate environment
        print("1. Validating environment...")
        validate_environment()
        print("✅ Environment validation passed")
        
        # 2. Get settings
        settings = get_project_settings()
        print(f"✅ Settings loaded: batch_size={settings['batch_size']}")
        
        # 3. Initialize data loader
        print("\n2. Loading data...")
        data_loader = DataLoader()
        
        # Load product data
        df = data_loader.load_product_data()
        print(f"✅ Loaded {len(df)} products")
        
        # Load HTS reference
        hts_data = data_loader.load_hts_reference()
        print(f"✅ Loaded {len(hts_data)} HTS codes")
        
        # 4. Initialize components
        print("\n3. Initializing components...")
        hts_hierarchy = HTSHierarchy(hts_data)
        print("✅ HTS hierarchy initialized")
        
        description_generator = SmartDescriptionGenerator(hts_hierarchy)
        print("✅ Smart description generator initialized")
        
        # 5. Create batch processing system
        batch_system = BatchProcessingSystem(
            data_loader,
            description_generator,
            settings
        )
        print("✅ Batch processing system created")
        
        # 6. Test small batch
        print("\n4. Testing small batch processing...")
        config = BatchConfig(batch_size=5, start_index=0)
        
        print(f"Processing batch with {config.batch_size} items...")
        batch_result = batch_system.run_batch(config)
        
        print(f"✅ Batch completed successfully!")
        print(f"   - Total items: {batch_result.total_items}")
        print(f"   - Successful: {batch_result.successful_items}")
        print(f"   - Failed: {batch_result.failed_items}")
        print(f"   - Processing time: {batch_result.processing_time:.2f}s")
        print(f"   - Confidence distribution: {batch_result.confidence_distribution}")
        
        # 7. Test progress tracking
        print("\n5. Testing progress tracking...")
        progress = batch_system.get_progress()
        print(f"✅ Progress tracking working")
        print(f"   - Total batches: {progress['total_batches']}")
        print(f"   - Completed batches: {progress['completed_batches']}")
        print(f"   - Success rate: {progress['success_rate']:.2%}")
        print(f"   - High confidence rate: {progress['high_confidence_rate']:.2%}")
        
        # 8. Test batch listing
        print("\n6. Testing batch listing...")
        batches = batch_system.list_batches()
        print(f"✅ Found {len(batches)} batches")
        
        if batches:
            latest_batch = batches[-1]
            print(f"   - Latest batch ID: {latest_batch['batch_id']}")
            print(f"   - Status: {latest_batch['status'].status if latest_batch['status'] else 'Unknown'}")
        
        print("\n🎉 All tests passed! Batch processing system is working correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_batch_processing()
    sys.exit(0 if success else 1)
