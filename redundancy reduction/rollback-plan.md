# Emergency Rollback Plan

## 🚨 Overview

This document provides step-by-step emergency rollback procedures for each phase of redundancy reduction. Use these procedures if critical issues arise that prevent the system from functioning correctly.

## 📋 General Rollback Principles

### Before Any Phase
Always create comprehensive backups before starting:

```bash
# Create backup directory
mkdir -p redundancy_reduction_backups/$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="redundancy_reduction_backups/$(date +%Y%m%d_%H%M%S)"

# Backup entire src directory
cp -r src/ "$BACKUP_DIR/src_backup/"

# Backup tests directory
cp -r tests/ "$BACKUP_DIR/tests_backup/"

# Create git branch for safety
git checkout -b redundancy_reduction_phase_1_backup
git add -A
git commit -m "Backup before Phase 1 redundancy reduction"
```

### Emergency Rollback Triggers

Immediately initiate rollback if any of these occur:
- Critical tests fail that were passing before
- System cannot start or import errors prevent basic functionality
- Data corruption or loss detected
- Performance degradation > 50%
- Any component completely non-functional

## 🔄 Phase 1 Rollback: Progress Tracking

### Scenario A: Import Errors After Consolidation

**Symptoms**: Import errors when trying to use batch processor or scaling components

**Quick Fix**:
```bash
# 1. Restore progress_tracker.py
cp redundancy_reduction_backups/*/src_backup/batch_processor/progress_tracker.py src/batch_processor/

# 2. Revert import changes in dynamic_scaling_controller.py
git checkout HEAD~1 -- src/batch_processor/dynamic_scaling_controller.py

# 3. Revert any other import changes
git checkout HEAD~1 -- src/batch_processor/batch_manager.py
git checkout HEAD~1 -- src/iterative_refinement_system.py

# 4. Test imports work
python -c "from src.batch_processor.progress_tracker import ProgressTracker; print('Import OK')"
```

### Scenario B: Scaling System Broken

**Symptoms**: Dynamic scaling controller fails to initialize or evaluate scaling

**Complete Rollback**:
```bash
# 1. Restore all original files
cp redundancy_reduction_backups/*/src_backup/batch_processor/progress_tracker.py src/batch_processor/
cp redundancy_reduction_backups/*/src_backup/batch_processor/dynamic_scaling_controller.py src/batch_processor/
cp redundancy_reduction_backups/*/src_backup/batch_processor/batch_manager.py src/batch_processor/

# 2. Test scaling functionality
python -m pytest tests/ -k "scaling" -v

# 3. If still failing, revert to git backup
git checkout redundancy_reduction_phase_1_backup -- src/
```

### Scenario C: Data Loss or Corruption

**Symptoms**: Metrics data missing, progress tracking not working, historical data lost

**Data Recovery**:
```bash
# 1. Stop all processes
pkill -f "python.*athena"

# 2. Restore entire progress tracking system
cp -r redundancy_reduction_backups/*/src_backup/batch_processor/ src/batch_processor/
cp -r redundancy_reduction_backups/*/src_backup/progress_tracking/ src/progress_tracking/

# 3. Restore data directory if needed
cp -r redundancy_reduction_backups/*/data_backup/ data/ 2>/dev/null || echo "No data backup found"

# 4. Verify data integrity
python -c "
import json
from pathlib import Path
data_dir = Path('data/metrics')
if data_dir.exists():
    files = list(data_dir.glob('*.json'))
    print(f'Found {len(files)} metrics files')
    for f in files[:3]:
        with open(f) as file:
            data = json.load(file)
            print(f'{f.name}: {len(data)} records')
else:
    print('No metrics directory found')
"
```

## 🔄 Phase 2 Rollback: Scaling Optimization

### Scenario A: Scaling Decisions Broken

**Symptoms**: Scaling manager fails to make decisions, predictor methods not working

**Quick Fix**:
```bash
# 1. Restore original scaling_predictor.py
cp redundancy_reduction_backups/*/src_backup/batch_processor/scaling_predictor.py src/batch_processor/

# 2. Revert scaling_manager.py changes
cp redundancy_reduction_backups/*/src_backup/batch_processor/scaling_manager.py src/batch_processor/

# 3. Revert dynamic_scaling_controller.py
cp redundancy_reduction_backups/*/src_backup/batch_processor/dynamic_scaling_controller.py src/batch_processor/

# 4. Test scaling prediction
python -c "
from src.batch_processor.scaling_predictor import ScalingPredictor
predictor = ScalingPredictor()
print('ScalingPredictor restored successfully')
"
```

### Scenario B: Enhanced ScalingManager Fails

**Symptoms**: New methods in ScalingManager cause errors, prediction logic broken

**Method-by-Method Rollback**:
```bash
# 1. Check which methods are failing
python -c "
from src.batch_processor.scaling_manager import ScalingManager
manager = ScalingManager()

# Test each enhanced method
methods_to_test = [
    'predict_optimal_batch_size',
    'should_scale_now', 
    'analyze_batch_size_efficiency',
    'predict_processing_time'
]

for method in methods_to_test:
    if hasattr(manager, method):
        print(f'✅ {method} exists')
    else:
        print(f'❌ {method} missing')
"

# 2. If methods are problematic, restore original and keep separate predictor
cp redundancy_reduction_backups/*/src_backup/batch_processor/scaling_manager.py src/batch_processor/
cp redundancy_reduction_backups/*/src_backup/batch_processor/scaling_predictor.py src/batch_processor/
```

### Scenario C: Performance Regression

**Symptoms**: Scaling evaluation takes significantly longer, memory usage increased

**Performance Rollback**:
```bash
# 1. Restore all original scaling files
cp redundancy_reduction_backups/*/src_backup/batch_processor/scaling_*.py src/batch_processor/

# 2. Run performance benchmark
python -c "
import time
from src.batch_processor.scaling_manager import ScalingManager

start = time.time()
manager = ScalingManager()

# Simulate scaling evaluations
for i in range(100):
    # Mock performance data
    performance = {
        'batch_size': 50,
        'high_confidence_rate': 0.8,
        'avg_processing_time': 2.0,
        'stability_score': 0.9
    }
    
    # This should be fast
    pass

duration = time.time() - start
print(f'Performance test completed in {duration:.2f}s')
if duration > 5.0:
    print('⚠️  Performance still slow after rollback')
else:
    print('✅ Performance restored')
"
```

## 🔄 Phase 3 Rollback: Minor Consolidations

### Scenario A: Notes Integration Broken

**Symptoms**: NotesManager missing integration methods, notes not being logged

**Quick Fix**:
```bash
# 1. Restore original notes files
cp redundancy_reduction_backups/*/src_backup/ai_analysis/notes_manager.py src/ai_analysis/
cp redundancy_reduction_backups/*/src_backup/ai_analysis/notes_integration.py src/ai_analysis/

# 2. Revert any import changes
git checkout HEAD~1 -- src/iterative_refinement_system.py

# 3. Test notes functionality
python -c "
from src.ai_analysis.notes_integration import NotesIntegration
integration = NotesIntegration()
print('Notes integration restored')
"
```

### Scenario B: Feedback Loop Oversimplified

**Symptoms**: Feedback processing missing functionality, orchestration broken

**Restore Full Feedback Loop**:
```bash
# 1. Restore original feedback_loop.py
cp redundancy_reduction_backups/*/src_backup/batch_processor/feedback_loop.py src/batch_processor/

# 2. Test feedback functionality
python -c "
from src.batch_processor.feedback_loop import FeedbackLoopManager
from pathlib import Path

manager = FeedbackLoopManager(Path('data'))
print('FeedbackLoopManager restored')

# Check for orchestration methods
methods = ['apply_rule_changes', 'get_improvement_trends']
for method in methods:
    if hasattr(manager, method):
        print(f'✅ {method} available')
    else:
        print(f'❌ {method} missing')
"
```

### Scenario C: Workflow Integration Issues

**Symptoms**: IterativeRefinementSystem cannot orchestrate components properly

**Complete Workflow Rollback**:
```bash
# 1. Restore all workflow-related files
cp redundancy_reduction_backups/*/src_backup/iterative_refinement_system.py src/
cp redundancy_reduction_backups/*/src_backup/batch_processor/feedback_loop.py src/batch_processor/
cp redundancy_reduction_backups/*/src_backup/ai_analysis/notes_*.py src/ai_analysis/

# 2. Test complete workflow
python -c "
from src.iterative_refinement_system import IterativeRefinementSystem
print('IterativeRefinementSystem restored')
"
```

## 🆘 Nuclear Option: Complete Rollback

### When to Use
- Multiple phases have failed
- System is completely non-functional
- Data corruption across multiple components
- Unable to identify specific failure point

### Complete System Restore

```bash
# 1. Stop all processes
pkill -f "python.*athena"

# 2. Restore entire codebase from backup
rm -rf src/
cp -r redundancy_reduction_backups/*/src_backup/ src/

# 3. Restore tests if needed
rm -rf tests/
cp -r redundancy_reduction_backups/*/tests_backup/ tests/

# 4. Or restore from git backup
git reset --hard redundancy_reduction_phase_1_backup

# 5. Clean up any generated files
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# 6. Run full test suite to verify restoration
python -m pytest tests/ -v

# 7. If tests still fail, check git history
git log --oneline -10
git checkout <known_good_commit>
```

## 🔍 Diagnostic Commands

### Quick Health Check

```bash
# Test basic imports
python -c "
try:
    from src.batch_processor.processor import BatchProcessor
    from src.progress_tracking.metrics_collector import MetricsCollector
    from src.ai_analysis.notes_manager import NotesManager
    from src.iterative_refinement_system import IterativeRefinementSystem
    print('✅ All core imports working')
except ImportError as e:
    print(f'❌ Import error: {e}')
"

# Test core functionality
python -c "
from src.iterative_refinement_system import IterativeRefinementSystem
from src.utils.data_loader import create_mock_data_loader
from src.utils.smart_description_generator import create_mock_generator

try:
    loader = create_mock_data_loader()
    generator = create_mock_generator()
    system = IterativeRefinementSystem(loader, generator)
    print('✅ Core system initializes')
except Exception as e:
    print(f'❌ System initialization error: {e}')
"
```

### Component Status Check

```bash
# Check which components exist
python -c "
import os
from pathlib import Path

components = [
    'src/batch_processor/progress_tracker.py',
    'src/batch_processor/scaling_predictor.py',
    'src/ai_analysis/notes_integration.py'
]

for component in components:
    if Path(component).exists():
        print(f'📁 {component} EXISTS (may indicate incomplete consolidation)')
    else:
        print(f'🗑️  {component} REMOVED (consolidated)')
"
```

## 📞 Emergency Contacts & Resources

### When to Escalate
- Complete system failure after rollback attempts
- Data corruption that cannot be recovered
- Performance issues persist after full rollback
- Unknown errors that don't match any scenario

### Recovery Resources
- **Backup Location**: `redundancy_reduction_backups/`
- **Git Backup Branch**: `redundancy_reduction_phase_X_backup`
- **Test Suite**: `python -m pytest tests/ -v`
- **Log Files**: Check `data/logs/system.log` for error details

### Validation Steps After Rollback
1. **Import Test**: All core modules import successfully
2. **Functionality Test**: Core workflows complete without errors
3. **Data Integrity**: Historical data accessible and correct
4. **Performance Test**: System performance within normal parameters
5. **Full Test Suite**: All automated tests pass

---

**Remember**: It's better to rollback early and replan than to push forward with a broken system. Document any issues encountered to improve future consolidation attempts.
