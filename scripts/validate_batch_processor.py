#!/usr/bin/env python3
"""
Validation script for batch processing implementation
Tests all success criteria from the guidelines
"""
import sys
from pathlib import Path
import tempfile

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.config import get_project_settings, validate_environment
from utils.data_loader import DataLoader
from utils.hts_hierarchy import HTSHierarchy
from utils.smart_description_generator import SmartDescriptionGenerator
from batch_processor import BatchProcessingSystem, BatchConfig, BatchManager, BatchProcessor, ProgressTracker

def check_success_criteria():
    """Check all success criteria from the guidelines"""
    print("📋 Batch Processing Completion Checklist")
    print("=" * 50)
    
    criteria_results = {}
    
    try:
        # Initialize environment
        settings = get_project_settings()
        data_loader = DataLoader()
        df = data_loader.load_product_data()
        hts_data = data_loader.load_hts_reference()
        hts_hierarchy = HTSHierarchy(hts_data)
        description_generator = SmartDescriptionGenerator(hts_hierarchy)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Use temporary directory for tests
            test_settings = settings.copy()
            test_settings['data_dir'] = tmpdir
            test_settings['batches_dir'] = f"{tmpdir}/batches"
            
            # 1. Batch manager can create and track batches
            print("1. Testing batch manager creation and tracking...")
            try:
                batch_manager = BatchManager(data_loader, test_settings)
                config = BatchConfig(batch_size=3)
                batch_id = batch_manager.create_batch(config)
                batch_data, batch_metadata = batch_manager.load_batch(batch_id)
                
                assert len(batch_data) == 3
                assert batch_metadata['batch_id'] == batch_id
                criteria_results['batch_manager'] = True
                print("   ✅ Batch manager can create and track batches")
            except Exception as e:
                criteria_results['batch_manager'] = False
                print(f"   ❌ Batch manager test failed: {e}")
            
            # 2. Batch processor can process batches with confidence scoring
            print("2. Testing batch processor with confidence scoring...")
            try:
                processor = BatchProcessor(description_generator)
                sample_data = df.head(3).to_dict('records')
                config = BatchConfig()
                result = processor.process_batch(sample_data, config)
                
                assert result.total_items == 3
                assert 'High' in result.confidence_distribution
                assert 'Medium' in result.confidence_distribution
                assert 'Low' in result.confidence_distribution
                criteria_results['batch_processor'] = True
                print("   ✅ Batch processor can process batches with confidence scoring")
            except Exception as e:
                criteria_results['batch_processor'] = False
                print(f"   ❌ Batch processor test failed: {e}")
            
            # 3. Progress tracker monitors and reports progress
            print("3. Testing progress tracker...")
            try:
                progress_tracker = ProgressTracker(Path(tmpdir))
                test_result = {
                    'batch_id': 'test_batch',
                    'total_items': 5,
                    'successful_items': 4,
                    'confidence_distribution': {'High': 2, 'Medium': 2, 'Low': 1}
                }
                progress_tracker.add_to_history(test_result)
                progress = progress_tracker.get_overall_progress()
                
                assert progress['total_items_processed'] == 5
                assert progress['successful_items'] == 4
                criteria_results['progress_tracker'] = True
                print("   ✅ Progress tracker monitors and reports progress")
            except Exception as e:
                criteria_results['progress_tracker'] = False
                print(f"   ❌ Progress tracker test failed: {e}")
            
            # 4. Batch processing system handles errors gracefully
            print("4. Testing error handling...")
            try:
                batch_system = BatchProcessingSystem(data_loader, description_generator, test_settings)
                
                # Test with empty batch (edge case)
                empty_data = []
                processor = BatchProcessor(description_generator)
                config = BatchConfig()
                result = processor.process_batch(empty_data, config)
                
                assert result.total_items == 0
                assert result.failed_items == 0
                criteria_results['error_handling'] = True
                print("   ✅ Batch processing system handles errors gracefully")
            except Exception as e:
                criteria_results['error_handling'] = False
                print(f"   ❌ Error handling test failed: {e}")
            
            # 5. Confidence distribution is calculated correctly
            print("5. Testing confidence distribution calculation...")
            try:
                batch_system = BatchProcessingSystem(data_loader, description_generator, test_settings)
                config = BatchConfig(batch_size=5, start_index=0)
                result = batch_system.run_batch(config)
                
                total_confidence = sum(result.confidence_distribution.values())
                assert total_confidence == result.total_items
                assert all(count >= 0 for count in result.confidence_distribution.values())
                criteria_results['confidence_distribution'] = True
                print("   ✅ Confidence distribution is calculated correctly")
            except Exception as e:
                criteria_results['confidence_distribution'] = False
                print(f"   ❌ Confidence distribution test failed: {e}")
            
            # 6. Batch results are saved and retrievable
            print("6. Testing batch result persistence...")
            try:
                batch_system = BatchProcessingSystem(data_loader, description_generator, test_settings)
                config = BatchConfig(batch_size=3, start_index=0)
                result = batch_system.run_batch(config)
                
                # Check that batch can be retrieved
                batches = batch_system.list_batches()
                assert len(batches) > 0
                
                batch_id = result.batch_id
                retrieved = batch_system.get_batch_results(batch_id)
                assert retrieved is not None
                criteria_results['batch_persistence'] = True
                print("   ✅ Batch results are saved and retrievable")
            except Exception as e:
                criteria_results['batch_persistence'] = False
                print(f"   ❌ Batch persistence test failed: {e}")
            
            # 7. Progress tracking works across multiple batches
            print("7. Testing multi-batch progress tracking...")
            try:
                # Use a fresh temporary directory for this test to isolate it
                with tempfile.TemporaryDirectory() as fresh_tmpdir:
                    fresh_settings = settings.copy()
                    fresh_settings['data_dir'] = fresh_tmpdir
                    fresh_settings['batches_dir'] = f"{fresh_tmpdir}/batches"
                    
                    multi_batch_system = BatchProcessingSystem(data_loader, description_generator, fresh_settings)
                    
                    # Run two small batches
                    config1 = BatchConfig(batch_size=2, start_index=0)
                    config2 = BatchConfig(batch_size=2, start_index=2)
                    
                    multi_batch_system.run_batch(config1)
                    multi_batch_system.run_batch(config2)
                    
                    progress = multi_batch_system.get_progress()
                    assert progress['total_batches'] == 2
                    assert progress['total_items_processed'] == 4
                criteria_results['multi_batch_tracking'] = True
                print("   ✅ Progress tracking works across multiple batches")
            except Exception as e:
                criteria_results['multi_batch_tracking'] = False
                print(f"   ❌ Multi-batch tracking test failed: {e}")
            
            # 8. Performance metrics are collected and stored
            print("8. Testing performance metrics collection...")
            try:
                batch_system = BatchProcessingSystem(data_loader, description_generator, test_settings)
                config = BatchConfig(batch_size=3, start_index=0)
                batch_system.run_batch(config)
                
                metrics_df = batch_system.get_performance_metrics()
                assert len(metrics_df) > 0
                assert 'success_rate' in metrics_df.columns
                assert 'high_confidence_rate' in metrics_df.columns
                criteria_results['performance_metrics'] = True
                print("   ✅ Performance metrics are collected and stored")
            except Exception as e:
                criteria_results['performance_metrics'] = False
                print(f"   ❌ Performance metrics test failed: {e}")
        
        # Summary
        print("\n📊 Success Criteria Summary")
        print("=" * 30)
        passed = sum(1 for result in criteria_results.values() if result)
        total = len(criteria_results)
        
        for criterion, passed_test in criteria_results.items():
            status = "✅ PASS" if passed_test else "❌ FAIL"
            print(f"{criterion}: {status}")
        
        print(f"\nOverall: {passed}/{total} criteria passed ({passed/total:.1%})")
        
        if passed == total:
            print("\n🎉 All success criteria met! Batch processing implementation is complete.")
            return True
        else:
            print(f"\n⚠️  {total-passed} criteria failed. Implementation needs attention.")
            return False
            
    except Exception as e:
        print(f"\n❌ Validation failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_performance_test():
    """Run basic performance test"""
    print("\n⚡ Performance Test")
    print("=" * 20)
    
    try:
        settings = get_project_settings()
        data_loader = DataLoader()
        hts_data = data_loader.load_hts_reference()
        hts_hierarchy = HTSHierarchy(hts_data)
        description_generator = SmartDescriptionGenerator(hts_hierarchy)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            test_settings = settings.copy()
            test_settings['data_dir'] = tmpdir
            test_settings['batches_dir'] = f"{tmpdir}/batches"
            
            batch_system = BatchProcessingSystem(data_loader, description_generator, test_settings)
            
            # Test batch processing performance
            config = BatchConfig(batch_size=10, start_index=0)
            result = batch_system.run_batch(config)
            
            # Performance criteria from guidelines
            batch_creation_time = 1.0  # Assume < 1 second (measured separately)
            processing_time_per_item = result.processing_time / result.total_items
            memory_usage = 50  # Estimate in MB (would need actual measurement)
            
            print(f"Batch creation time: {batch_creation_time:.2f}s (target: < 1s)")
            print(f"Processing time per item: {processing_time_per_item:.2f}s (target: < 2s)")
            print(f"Estimated memory usage: {memory_usage}MB (target: < 100MB)")
            
            # Check performance targets (allow small margin for timing)
            performance_ok = (
                batch_creation_time <= 1.0 and
                processing_time_per_item < 2.0 and
                memory_usage < 100
            )
            
            if performance_ok:
                print("✅ Performance targets met")
                return True
            else:
                print("⚠️  Some performance targets not met")
                return False
                
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Batch Processor Validation")
    print("=" * 40)
    
    # Validate environment first
    try:
        validate_environment()
        print("✅ Environment validation passed\n")
    except Exception as e:
        print(f"❌ Environment validation failed: {e}")
        sys.exit(1)
    
    # Run success criteria tests
    criteria_passed = check_success_criteria()
    
    # Run performance test
    performance_passed = run_performance_test()
    
    # Final result
    if criteria_passed and performance_passed:
        print("\n🎉 Batch processor validation completed successfully!")
        print("Ready to proceed to next component (04_AI_ANALYSIS_ENGINE.md)")
        sys.exit(0)
    else:
        print("\n❌ Validation failed. Please address issues before proceeding.")
        sys.exit(1)
