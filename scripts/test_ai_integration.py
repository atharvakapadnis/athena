#!/usr/bin/env python3
"""
AI Integration Test for Iterative Refinement System

This script tests the real OpenAI AI client integration to ensure
the system can properly analyze patterns and suggest rules.
"""

import sys
import os
from pathlib import Path
import json
import tempfile
import shutil
from datetime import datetime

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Import components
try:
    from ai_analysis import AIClient, PatternAnalyzer, RuleSuggester, AnalysisAggregator
    from utils.logger import get_logger
    
    print("✓ Successfully imported AI analysis components")
except ImportError as e:
    print(f"✗ Failed to import AI components: {e}")
    sys.exit(1)

logger = get_logger(__name__)

class AIIntegrationTest:
    """Test real AI integration functionality"""
    
    def __init__(self):
        self.test_results = {
            'tests_passed': 0,
            'tests_failed': 0,
            'errors': []
        }
    
    def test_ai_client_initialization(self):
        """Test that AI client can be initialized with real API key"""
        print("\n🤖 Testing AI Client Initialization...")
        
        try:
            # Check if API key is available
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                print("  ✗ No OPENAI_API_KEY found in environment")
                print("  ℹ️  Make sure your .env file contains: OPENAI_API_KEY=your_key_here")
                self.record_test_fail("AI Client Initialization", "No API key found")
                return False
            
            print(f"  ✓ Found API key: {api_key[:8]}...{api_key[-4:] if len(api_key) > 12 else '***'}")
            
            # Initialize AI client
            ai_client = AIClient()
            print("  ✓ AI Client initialized successfully")
            
            self.record_test_pass("AI Client Initialization")
            return ai_client
            
        except Exception as e:
            print(f"  ✗ AI Client initialization failed: {e}")
            self.record_test_fail("AI Client Initialization", str(e))
            return None
    
    def test_pattern_analysis(self, ai_client):
        """Test AI pattern analysis functionality"""
        print("\n🔍 Testing AI Pattern Analysis...")
        
        if not ai_client:
            print("  ⏭️  Skipping - no AI client available")
            return
        
        try:
            # Create sample low-confidence results for analysis
            sample_low_confidence_results = [
                {
                    'item_id': 'TEST001',
                    'original_description': 'DI SPACER 6X4 MJ',
                    'enhanced_description': 'spacer 6x4',
                    'confidence_score': 0.3,
                    'confidence_level': 'Low',
                    'extracted_features': {'material': '', 'size': '6x4'},
                    'issues': ['missing material identification', 'incomplete description']
                },
                {
                    'item_id': 'TEST002',
                    'original_description': 'SS ELBOW 90 DEG 4 INCH',
                    'enhanced_description': 'elbow 4 inch',
                    'confidence_score': 0.4,
                    'confidence_level': 'Low',
                    'extracted_features': {'material': '', 'size': '4 inch'},
                    'issues': ['missing material identification', 'missing degree specification']
                }
            ]
            
            print(f"  ➤ Analyzing {len(sample_low_confidence_results)} low-confidence results...")
            
            # Call AI analysis
            analysis_result = ai_client.analyze_failure_patterns(sample_low_confidence_results)
            
            print(f"  ✓ AI analysis completed")
            print(f"  ✓ Analysis keys: {list(analysis_result.keys())}")
            
            # Check if we got meaningful results
            if 'error' in analysis_result:
                print(f"  ⚠️  AI returned error: {analysis_result['error']}")
                self.record_test_fail("AI Pattern Analysis", analysis_result['error'])
            else:
                print(f"  ✓ AI analysis successful")
                if 'patterns' in analysis_result:
                    print(f"  ✓ Found patterns: {analysis_result.get('patterns', [])[:3]}...")
                
                self.record_test_pass("AI Pattern Analysis")
                return analysis_result
            
        except Exception as e:
            print(f"  ✗ AI pattern analysis failed: {e}")
            self.record_test_fail("AI Pattern Analysis", str(e))
            return None
    
    def test_rule_suggestions(self, ai_client):
        """Test AI rule suggestion functionality"""
        print("\n📝 Testing AI Rule Suggestions...")
        
        if not ai_client:
            print("  ⏭️  Skipping - no AI client available")
            return
        
        try:
            # Create sample failure patterns for rule suggestion
            sample_failure_patterns = {
                'common_issues': [
                    'missing material identification',
                    'incomplete size specifications',
                    'missing connection type details'
                ],
                'patterns': [
                    'Material abbreviations not being expanded (DI, SS, CI)',
                    'Size information present but not properly formatted',
                    'Technical specifications missing from descriptions'
                ],
                'examples': [
                    {'original': 'DI SPACER 6X4 MJ', 'issue': 'DI not expanded to ductile iron'},
                    {'original': 'SS ELBOW 90 DEG', 'issue': 'SS not expanded to stainless steel'}
                ]
            }
            
            print(f"  ➤ Requesting rule suggestions for identified patterns...")
            
            # Call AI rule suggestion
            rule_suggestions = ai_client.suggest_rules(sample_failure_patterns)
            
            print(f"  ✓ AI rule suggestion completed")
            print(f"  ✓ Received {len(rule_suggestions)} rule suggestions")
            
            # Display first few suggestions
            for i, suggestion in enumerate(rule_suggestions[:2]):
                print(f"  ✓ Suggestion {i+1}: {suggestion.get('rule_type', 'unknown')} - {suggestion.get('pattern', 'no pattern')}")
            
            self.record_test_pass("AI Rule Suggestions")
            return rule_suggestions
            
        except Exception as e:
            print(f"  ✗ AI rule suggestions failed: {e}")
            self.record_test_fail("AI Rule Suggestions", str(e))
            return None
    
    def test_analysis_aggregator(self, ai_client):
        """Test the complete analysis aggregator with real AI"""
        print("\n📊 Testing Analysis Aggregator with Real AI...")
        
        if not ai_client:
            print("  ⏭️  Skipping - no AI client available")
            return
        
        try:
            # Create temporary directory for testing
            temp_dir = Path(tempfile.mkdtemp(prefix="ai_integration_test_"))
            
            # Initialize analysis aggregator with real AI client
            analysis_aggregator = AnalysisAggregator(ai_client, temp_dir)
            
            print("  ✓ Analysis aggregator initialized with real AI client")
            
            # Create sample batch results
            sample_batch_results = [
                {
                    'item_id': 'TEST001',
                    'original_description': 'DI SPACER 6X4 MJ',
                    'enhanced_description': 'spacer fitting',
                    'confidence_score': 0.3,
                    'confidence_level': 'Low',
                    'success': True
                },
                {
                    'item_id': 'TEST002',
                    'original_description': 'SS ELBOW 90 DEG 4 INCH',
                    'enhanced_description': 'elbow fitting',
                    'confidence_score': 0.35,
                    'confidence_level': 'Low',
                    'success': True
                },
                {
                    'item_id': 'TEST003',
                    'original_description': 'CI VALVE BALL 6 INCH',
                    'enhanced_description': 'ball valve 6 inch cast iron',
                    'confidence_score': 0.85,
                    'confidence_level': 'High',
                    'success': True
                }
            ]
            
            print(f"  ➤ Running complete analysis on {len(sample_batch_results)} results...")
            
            # Run complete analysis
            complete_analysis = analysis_aggregator.analyze_batch_results(sample_batch_results)
            
            print("  ✓ Complete analysis finished")
            print(f"  ✓ Analysis contains: {list(complete_analysis.keys())}")
            
            # Check analysis results
            if 'rule_suggestions' in complete_analysis:
                suggestions_count = len(complete_analysis['rule_suggestions'])
                print(f"  ✓ Generated {suggestions_count} rule suggestions")
            
            if 'insights' in complete_analysis:
                insights_count = len(complete_analysis['insights'])
                print(f"  ✓ Generated {insights_count} insights")
            
            # Clean up
            shutil.rmtree(temp_dir)
            
            self.record_test_pass("Analysis Aggregator with Real AI")
            return complete_analysis
            
        except Exception as e:
            print(f"  ✗ Analysis aggregator test failed: {e}")
            self.record_test_fail("Analysis Aggregator with Real AI", str(e))
            return None
    
    def test_end_to_end_ai_workflow(self):
        """Test complete end-to-end AI workflow"""
        print("\n🔄 Testing End-to-End AI Workflow...")
        
        try:
            # Step 1: Initialize AI client
            ai_client = self.test_ai_client_initialization()
            if not ai_client:
                print("  ⏭️  Skipping end-to-end test - AI client not available")
                return
            
            # Step 2: Test pattern analysis
            pattern_analysis = self.test_pattern_analysis(ai_client)
            
            # Step 3: Test rule suggestions
            rule_suggestions = self.test_rule_suggestions(ai_client)
            
            # Step 4: Test analysis aggregator
            complete_analysis = self.test_analysis_aggregator(ai_client)
            
            if pattern_analysis and rule_suggestions and complete_analysis:
                print("\n  🎉 End-to-end AI workflow completed successfully!")
                self.record_test_pass("End-to-End AI Workflow")
            else:
                print("\n  ⚠️  End-to-end workflow had some issues")
                self.record_test_fail("End-to-End AI Workflow", "Some components failed")
            
        except Exception as e:
            print(f"\n  ✗ End-to-end workflow failed: {e}")
            self.record_test_fail("End-to-End AI Workflow", str(e))
    
    def record_test_pass(self, test_name):
        """Record a successful test"""
        self.test_results['tests_passed'] += 1
        print(f"  ✅ PASS: {test_name}")
    
    def record_test_fail(self, test_name, error_message):
        """Record a failed test"""
        self.test_results['tests_failed'] += 1
        self.test_results['errors'].append({
            'test': test_name,
            'error': error_message,
            'timestamp': datetime.now().isoformat()
        })
        print(f"  ❌ FAIL: {test_name} - {error_message}")
    
    def run_all_tests(self):
        """Run all AI integration tests"""
        print("🤖 Starting AI Integration Tests")
        print("=" * 60)
        
        # Check environment
        print(f"🔧 Environment Check:")
        print(f"  - Python: {sys.version.split()[0]}")
        print(f"  - Working Directory: {os.getcwd()}")
        print(f"  - OpenAI API Key: {'✓ Found' if os.getenv('OPENAI_API_KEY') else '✗ Not Found'}")
        
        try:
            self.test_end_to_end_ai_workflow()
            
        except Exception as e:
            print(f"\n💥 Critical test failure: {e}")
            self.test_results['critical_error'] = str(e)
        
        # Generate test summary
        self.generate_test_summary()
    
    def generate_test_summary(self):
        """Generate and display test summary"""
        total_tests = self.test_results['tests_passed'] + self.test_results['tests_failed']
        success_rate = (self.test_results['tests_passed'] / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "=" * 60)
        print("🎯 AI INTEGRATION TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {self.test_results['tests_passed']} ✅")
        print(f"Failed: {self.test_results['tests_failed']} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if self.test_results['errors']:
            print("\n❌ FAILED TESTS:")
            for error in self.test_results['errors']:
                print(f"  - {error['test']}: {error['error']}")
        
        if success_rate >= 80:
            print("\n🎉 AI INTEGRATION WORKING! Real OpenAI client is operational.")
        else:
            print("\n🚨 AI Integration needs attention. Check API key and network connection.")
        
        print("=" * 60)

def main():
    """Main test execution"""
    test_runner = AIIntegrationTest()
    test_runner.run_all_tests()

if __name__ == "__main__":
    main()

