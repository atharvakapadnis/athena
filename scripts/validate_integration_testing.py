#!/usr/bin/env python3
"""
Quick validation script for the integration testing system

This script performs a basic validation to ensure the integration testing
system is properly set up and can be imported and initialized.
"""

import sys
import os
from pathlib import Path

# Add project root and src directory to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

def main():
    """Main validation function"""
    print("Validating Integration Testing System Setup...")
    print("=" * 50)
    
    validation_results = {
        'imports': False,
        'initialization': False,
        'test_data_generation': False,
        'mock_functionality': False
    }
    
    try:
        # Test imports
        print("1. Testing imports...")
        from integration_testing import (
            SystemIntegrationTester,
            ComponentInteractionTester,
            PerformanceIntegrationTester,
            IntegrationTestRunner,
            TestDataGenerator,
            TestResult
        )
        validation_results['imports'] = True
        print("   ✓ All integration testing components imported successfully")
        
        # Test initialization
        print("\n2. Testing initialization...")
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            test_settings = {
                'data_dir': tmpdir,
                'input_dir': f"{tmpdir}/input",
                'batch_size': 5
            }
            
            # Create input directory
            input_dir = Path(tmpdir) / "input"
            input_dir.mkdir(exist_ok=True)
            
            # Test each component initialization
            system_tester = SystemIntegrationTester(test_settings)
            component_tester = ComponentInteractionTester(test_settings)
            performance_tester = PerformanceIntegrationTester(test_settings)
            test_runner = IntegrationTestRunner(test_settings)
            
            validation_results['initialization'] = True
            print("   ✓ All integration testing components initialized successfully")
            
            # Test test data generation
            print("\n3. Testing test data generation...")
            test_generator = TestDataGenerator()
            
            # Test mock data loader
            mock_loader = test_generator.create_mock_data_loader()
            assert mock_loader is not None
            product_data = mock_loader.load_product_data()
            assert product_data is not None and len(product_data) > 0
            
            # Test mock description generator
            mock_generator = test_generator.create_mock_description_generator()
            assert mock_generator is not None
            test_product = {
                'item_id': 'test_001',
                'item_description': 'Test product',
                'material_detail': 'steel'
            }
            result = mock_generator.generate_description(test_product)
            assert result is not None
            assert hasattr(result, 'confidence_score')
            assert 0 <= result.confidence_score <= 1
            
            # Test mock AI client
            mock_ai_client = test_generator.create_mock_ai_client()
            assert mock_ai_client is not None
            test_results = [{'confidence_level': 'Low'}]
            analysis = mock_ai_client.analyze_failure_patterns(test_results)
            assert analysis is not None
            assert 'patterns' in analysis
            
            validation_results['test_data_generation'] = True
            print("   ✓ Test data generation working correctly")
            
            # Test basic mock functionality
            print("\n4. Testing mock functionality...")
            
            # Test test rule creation
            test_rule = test_generator.create_test_rule()
            assert test_rule is not None
            assert 'rule_id' in test_rule
            assert test_rule['metadata']['test_rule'] is True
            
            # Test mock processing results
            processing_results = test_generator.create_mock_processing_results()
            assert processing_results is not None
            assert len(processing_results) > 0
            for result in processing_results:
                assert 'confidence_score' in result
                assert 0 <= result['confidence_score'] <= 1
            
            validation_results['mock_functionality'] = True
            print("   ✓ Mock functionality working correctly")
        
        # Overall validation result
        print("\n" + "=" * 50)
        print("VALIDATION RESULTS:")
        print("=" * 50)
        
        all_passed = all(validation_results.values())
        
        for check, passed in validation_results.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"  {check.replace('_', ' ').title()}: {status}")
        
        print(f"\nOVERALL STATUS: {'✓ ALL CHECKS PASSED' if all_passed else '✗ SOME CHECKS FAILED'}")
        
        if all_passed:
            print("\nIntegration testing system is ready for use!")
            print("You can now run:")
            print("  python scripts/run_integration_tests.py --type quick")
            print("  python scripts/run_integration_tests.py --type all")
        else:
            print("\nSome validation checks failed. Please review the errors above.")
        
        return 0 if all_passed else 1
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        print("Please ensure all dependencies are installed and the project structure is correct.")
        return 1
        
    except Exception as e:
        print(f"✗ Validation error: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
