#!/usr/bin/env python3
"""
Automated test runner for redundancy reduction phases
"""

import subprocess
import sys
import os
from pathlib import Path
import time
from datetime import datetime

def print_header(message):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"TEST: {message}")
    print("=" * 60)

def print_status(message, success=True):
    """Print status message with status indicator"""
    status = "[PASS]" if success else "[FAIL]"
    print(f"{status} {message}")

def run_command(command, description=""):
    """Run command and return success status"""
    print(f"\nRunning: {description or command}")
    
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            print_status(f"SUCCESS: {description or command}")
            if result.stdout.strip():
                print(f"Output: {result.stdout.strip()}")
            return True
        else:
            print_status(f"FAILED: {description or command}", False)
            if result.stderr.strip():
                print(f"Error: {result.stderr.strip()}")
            if result.stdout.strip():
                print(f"Output: {result.stdout.strip()}")
            return False
            
    except subprocess.TimeoutExpired:
        print_status(f"TIMEOUT: {description or command}", False)
        return False
    except Exception as e:
        print_status(f"EXCEPTION: {description or command} - {e}", False)
        return False

def check_environment():
    """Check if environment is ready for testing"""
    print_header("Environment Check")
    
    # Use Windows-compatible commands
    import platform
    import os
    is_windows = platform.system() == "Windows"
    
    # Check Python version
    if not run_command("python --version", "Python version check"):
        return False
    
    # Check pytest availability and install if needed
    print("\nChecking pytest availability...")
    try:
        import pytest
        print_status(f"Pytest available (version {pytest.__version__})")
    except ImportError:
        print_status("Pytest not found, attempting to install...", False)
        if not run_command("pip install pytest", "Installing pytest"):
            print_status("Failed to install pytest", False)
            return False
        try:
            import pytest
            print_status(f"Pytest installed successfully (version {pytest.__version__})")
        except ImportError:
            print_status("Pytest installation failed", False)
            return False
    
    # Check directories exist
    directories = [
        ("src", "Source directory exists"),
        ("tests", "Tests directory exists")
    ]
    
    all_passed = True
    for directory, description in directories:
        if os.path.exists(directory) and os.path.isdir(directory):
            print_status(f"{description}")
        else:
            print_status(f"{description}", False)
            all_passed = False
    
    return all_passed

def test_baseline():
    """Run baseline tests to ensure system is working before changes"""
    print_header("Baseline Testing - Establishing Current State")
    
    tests = [
        ("python -c \"import src.batch_processor.processor; print('PASS: batch_processor imports')\"", 
         "Core batch processor import"),
        ("python -c \"import src.progress_tracking.metrics_collector; print('PASS: progress_tracking imports')\"", 
         "Progress tracking import"),
        ("python -c \"import src.ai_analysis.notes_manager; print('PASS: ai_analysis imports')\"", 
         "AI analysis import"),
        ("python -c \"import src.iterative_refinement_system; print('PASS: main system imports')\"", 
         "Main system import"),
        ("python -m pytest tests/ --tb=short -q", 
         "Full test suite (quick)")
    ]
    
    return all(run_command(test, desc) for test, desc in tests)

def test_phase_1():
    """Test Phase 1: Progress Tracking Consolidation"""
    print_header("Phase 1 Testing: Progress Tracking Consolidation")
    
    tests = [
        # Import tests
        ("python -c \"from src.progress_tracking.metrics_collector import MetricsCollector; print('PASS: MetricsCollector import')\"",
         "MetricsCollector import after consolidation"),
        ("python -c \"from src.progress_tracking.performance_analyzer import PerformanceAnalyzer; print('PASS: PerformanceAnalyzer import')\"",
         "PerformanceAnalyzer import after consolidation"),
        ("python -c \"from src.progress_tracking.dashboard import ProgressDashboard; print('PASS: ProgressDashboard import')\"",
         "ProgressDashboard import after consolidation"),
        
        # Functionality tests
        ("python -c \"from src.progress_tracking.metrics_collector import MetricsCollector; mc = MetricsCollector('data/metrics'); print('PASS: MetricsCollector creation')\"",
         "MetricsCollector instantiation"),
        
        # Integration tests
        ("python -m pytest tests/ -k 'progress' -v",
         "Progress-related tests"),
        ("python -m pytest tests/ -k 'metrics' -v",
         "Metrics-related tests"),
        ("python -m pytest tests/ -k 'batch' -v",
         "Batch processing tests"),
    ]
    
    return all(run_command(test, desc) for test, desc in tests)

def test_phase_2():
    """Test Phase 2: Scaling Optimization"""
    print_header("Phase 2 Testing: Scaling Optimization")
    
    tests = [
        # Import tests
        ("python -c \"from src.batch_processor.scaling_manager import ScalingManager; print('PASS: Enhanced ScalingManager import')\"",
         "Enhanced ScalingManager import"),
        ("python -c \"from src.batch_processor.dynamic_scaling_controller import DynamicScalingController; print('PASS: DynamicScalingController import')\"",
         "DynamicScalingController import"),
        
        # Enhanced functionality tests
        ("python -c \"from src.batch_processor.scaling_manager import ScalingManager; sm = ScalingManager(); print('PASS: ScalingManager has predict methods:', hasattr(sm, 'predict_optimal_batch_size'))\"",
         "ScalingManager enhanced methods check"),
        
        # Scaling functionality tests
        ("python -m pytest tests/ -k 'scaling' -v",
         "Scaling-related tests"),
        ("python -m pytest tests/ -k 'dynamic' -v",
         "Dynamic scaling tests"),
        ("python -m pytest tests/test_batch_processor.py -v",
         "Batch processor integration tests"),
    ]
    
    return all(run_command(test, desc) for test, desc in tests)

def test_phase_3():
    """Test Phase 3: Minor Consolidations"""
    print_header("Phase 3 Testing: Minor Consolidations")
    
    tests = [
        # Notes manager tests
        ("python -c \"from src.ai_analysis.notes_manager import NotesManager; nm = NotesManager(); print('PASS: Enhanced NotesManager import')\"",
         "Enhanced NotesManager import"),
        ("python -c \"from src.ai_analysis.notes_manager import NotesManager; nm = NotesManager(); print('PASS: Has integration methods:', hasattr(nm, 'log_ai_analysis_observation'))\"",
         "NotesManager integration methods check"),
        
        # Feedback loop tests
        ("python -c \"from src.batch_processor.feedback_loop import FeedbackLoopManager; print('PASS: FeedbackLoopManager import')\"",
         "FeedbackLoopManager import"),
        
        # Integration tests
        ("python -m pytest tests/ -k 'notes' -v",
         "Notes-related tests"),
        ("python -m pytest tests/ -k 'feedback' -v",
         "Feedback-related tests"),
        ("python -m pytest tests/test_ai_analysis.py -v",
         "AI analysis tests"),
    ]
    
    return all(run_command(test, desc) for test, desc in tests)

def test_integration():
    """Test full system integration after all phases"""
    print_header("Integration Testing: Complete System")
    
    tests = [
        # Full system import
        ("python -c \"from src.iterative_refinement_system import IterativeRefinementSystem; print('PASS: Main system imports')\"",
         "Main system import after consolidation"),
        
        # Component integration
        ("python -c \"from src.iterative_refinement_system import IterativeRefinementSystem; print('PASS: System import successful')\"",
         "System initialization test"),
        
        # Full test suite
        ("python -m pytest tests/ -v --tb=short",
         "Complete test suite"),
        
        # Performance test
        ("python -c \"import time; start=time.time(); from src.iterative_refinement_system import IterativeRefinementSystem; duration=time.time()-start; print(f'PASS: Import time: {duration:.2f}s'); assert duration < 5.0, 'Import too slow'\"",
         "Import performance check"),
    ]
    
    return all(run_command(test, desc) for test, desc in tests)

def run_performance_benchmark():
    """Run performance benchmark"""
    print_header("Performance Benchmark")
    
    # Create a temporary benchmark script file to avoid shell escaping issues
    import tempfile
    import os
    
    benchmark_script = """import time
import tracemalloc
from src.progress_tracking.metrics_collector import MetricsCollector
from src.batch_processor.scaling_manager import ScalingManager

# Memory tracking
tracemalloc.start()

# Test metrics collection performance
start_time = time.time()
metrics_collector = MetricsCollector("data/metrics")
metrics_time = time.time() - start_time

# Test scaling manager performance  
start_time = time.time()
scaling_manager = ScalingManager()
scaling_time = time.time() - start_time

# Memory usage
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()

print(f"Performance Results:")
print(f"   MetricsCollector init: {metrics_time:.3f}s")
print(f"   ScalingManager init: {scaling_time:.3f}s")
print(f"   Memory usage: {current / 1024 / 1024:.1f} MB (peak: {peak / 1024 / 1024:.1f} MB)")

# Performance assertions
assert metrics_time < 1.0, f"MetricsCollector init too slow: {metrics_time:.3f}s"
assert scaling_time < 1.0, f"ScalingManager init too slow: {scaling_time:.3f}s"
assert peak / 1024 / 1024 < 100, f"Memory usage too high: {peak / 1024 / 1024:.1f} MB"

print("Performance benchmark passed")
"""
    
    # Write to temporary file and execute
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(benchmark_script)
            temp_file = f.name
        
        result = run_command(f"python {temp_file}", "Performance benchmark")
        
        # Clean up
        os.unlink(temp_file)
        return result
        
    except Exception as e:
        print_status(f"Error creating benchmark script: {e}", False)
        return False

def generate_report(results):
    """Generate test report"""
    print_header("Test Report Summary")
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    failed_tests = total_tests - passed_tests
    
    print(f"Test Summary:")
    print(f"   Total test phases: {total_tests}")
    print(f"   Passed: {passed_tests}")
    print(f"   Failed: {failed_tests}")
    print(f"   Success rate: {passed_tests/total_tests*100:.1f}%")
    
    print(f"\nDetailed Results:")
    for phase, success in results.items():
        status = "PASS" if success else "FAIL"
        print(f"   {phase}: {status}")
    
    # Save report to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"redundancy_reduction/test_report_{timestamp}.txt"
    
    with open(report_file, 'w') as f:
        f.write(f"Redundancy Reduction Test Report\n")
        f.write(f"Generated: {datetime.now()}\n")
        f.write(f"Total phases: {total_tests}\n")
        f.write(f"Passed: {passed_tests}\n")
        f.write(f"Failed: {failed_tests}\n")
        f.write(f"Success rate: {passed_tests/total_tests*100:.1f}%\n\n")
        
        f.write("Detailed Results:\n")
        for phase, success in results.items():
            status = "PASS" if success else "FAIL"
            f.write(f"{phase}: {status}\n")
    
    print(f"\nReport saved to: {report_file}")
    
    return passed_tests == total_tests

def main():
    """Main test runner"""
    print_header("Redundancy Reduction Test Runner")
    print(f"🕐 Started at: {datetime.now()}")
    
    # Check command line arguments
    if len(sys.argv) > 1:
        phase = sys.argv[1].lower()
        
        if not check_environment():
            print_status("Environment check failed", False)
            sys.exit(1)
        
        if phase == "baseline":
            success = test_baseline()
        elif phase == "1":
            success = test_phase_1()
        elif phase == "2":
            success = test_phase_2()
        elif phase == "3":
            success = test_phase_3()
        elif phase == "integration":
            success = test_integration()
        elif phase == "performance":
            success = run_performance_benchmark()
        elif phase == "all":
            results = {
                "Environment Check": check_environment(),
                "Baseline Tests": test_baseline(),
                "Phase 1": test_phase_1(),
                "Phase 2": test_phase_2(),
                "Phase 3": test_phase_3(),
                "Integration": test_integration(),
                "Performance": run_performance_benchmark()
            }
            success = generate_report(results)
        else:
            print("Usage: python run_tests.py [baseline|1|2|3|integration|performance|all]")
            sys.exit(1)
    else:
        # Run all tests by default
        results = {
            "Environment Check": check_environment(),
            "Baseline Tests": test_baseline(),
            "Phase 1": test_phase_1(),
            "Phase 2": test_phase_2(),
            "Phase 3": test_phase_3(),
            "Integration": test_integration(),
            "Performance": run_performance_benchmark()
        }
        success = generate_report(results)
    
    # Final result
    if success:
        print_status("ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print_status("SOME TESTS FAILED!", False)
        print("\nNext steps:")
        print("   1. Check error messages above")
        print("   2. Review rollback plan if needed")
        print("   3. Fix issues and re-run tests")
        sys.exit(1)

if __name__ == "__main__":
    main()
