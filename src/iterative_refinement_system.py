# src/iterative_refinement_system.py
"""
Iterative Refinement System - Main Orchestrator

This is the core system that orchestrates the iterative improvement workflow,
tying together all components: batch processing, feedback collection, AI analysis,
rule management, and quality monitoring.
"""

from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
import json

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import all the components
from batch_processor import BatchProcessingSystem, BatchConfig, FeedbackLoopManager, RefinementAction
from ai_analysis import AnalysisAggregator, RuleSuggester, PatternAnalyzer
from rule_editor import RuleManager, ApprovalWorkflow, RuleValidator, RuleImpactAnalyzer
from confidence_scoring import ConfidenceScoringSystem
from progress_tracking import QualityMonitor
from utils.logger import get_logger
from utils.config import get_project_settings

logger = get_logger(__name__)

class IterativeRefinementSystem:
    """
    Main orchestrator for the iterative refinement system
    
    This class coordinates the entire workflow:
    1. Process batches with confidence scoring
    2. Collect feedback and identify improvement opportunities  
    3. Analyze patterns and suggest rules via AI
    4. Get human approval for rule changes
    5. Apply approved rules and measure impact
    6. Monitor quality trends and adjust strategy
    """
    
    def __init__(self, data_loader, description_generator, settings: Dict[str, Any] = None):
        """Initialize the iterative refinement system"""
        self.settings = settings or get_project_settings()
        self.data_dir = Path(self.settings['data_dir'])
        
        # Initialize core components
        self.batch_system = BatchProcessingSystem(data_loader, description_generator, self.settings)
        
        # Initialize rule management
        self.rule_manager = RuleManager(self.data_dir / "rules")
        
        # Get existing rules for validator (start with empty list if none exist)
        try:
            existing_rules = self.rule_manager.list_rules()
        except:
            existing_rules = []
            
        self.rule_validator = RuleValidator(existing_rules)
        self.approval_workflow = ApprovalWorkflow(self.rule_manager, self.rule_validator)
        
        # Initialize feedback and quality monitoring
        self.feedback_manager = FeedbackLoopManager(
            self.data_dir, 
            self.rule_manager, 
            self.approval_workflow
        )
        self.quality_monitor = QualityMonitor(self.data_dir)
        self.rule_analyzer = RuleImpactAnalyzer(self.data_dir)
        
        # Initialize AI analysis components
        # Try to create AI client, use mock if API key not available
        try:
            from ai_analysis import AIClient
            ai_client = AIClient()
        except (ValueError, Exception) as e:
            logger.warning(f"Could not initialize AI client: {e}. Using mock client for testing.")
            # Create a simple mock AI client for testing
            class MockAIClient:
                def suggest_rules(self, failure_patterns):
                    return [
                        {
                            'rule_type': 'enhancement',
                            'pattern': 'test_pattern',
                            'replacement': 'test_replacement',
                            'confidence': 0.8,
                            'reasoning': 'Mock suggestion for testing',
                            'examples': ['test example']
                        }
                    ]
                
                def analyze_failure_patterns(self, low_confidence_results):
                    return {
                        'patterns': ['test_pattern'],
                        'common_issues': ['test_issue'],
                        'suggestions': ['test_suggestion']
                    }
            
            ai_client = MockAIClient()
        
        self.analysis_aggregator = AnalysisAggregator(ai_client, self.data_dir)
        self.rule_suggester = RuleSuggester(ai_client)
        self.pattern_analyzer = PatternAnalyzer()
        
        # Initialize confidence scoring
        self.confidence_system = ConfidenceScoringSystem()
        
        # System state
        self.current_iteration = 0
        self.system_metrics = {}
        
        logger.info("Iterative Refinement System initialized")
    
    def run_iterative_cycle(self, batch_config: BatchConfig, iteration_name: str = None) -> Dict[str, Any]:
        """
        Run a complete iterative refinement cycle
        
        Returns comprehensive results of the iteration including all analysis and recommendations
        """
        iteration_name = iteration_name or f"iteration_{self.current_iteration + 1}"
        self.current_iteration += 1
        
        logger.info(f"Starting iterative cycle: {iteration_name}")
        
        cycle_results = {
            'iteration_name': iteration_name,
            'iteration_number': self.current_iteration,
            'start_time': datetime.now().isoformat(),
            'batch_results': None,
            'feedback_summary': None,
            'quality_metrics': None,
            'ai_analysis': None,
            'rule_suggestions': None,
            'improvement_opportunities': [],
            'recommendations': [],
            'cycle_summary': {}
        }
        
        try:
            # Step 1: Run batch processing
            logger.info("Step 1: Running batch processing")
            batch_result = self.batch_system.run_batch(batch_config)
            cycle_results['batch_results'] = self._serialize_batch_result(batch_result)
            
            # Step 2: Process feedback
            logger.info("Step 2: Processing batch feedback")
            feedback_summary = self.feedback_manager.process_batch_feedback(batch_result)
            cycle_results['feedback_summary'] = self._serialize_feedback_summary(feedback_summary)
            
            # Step 3: Track quality metrics
            logger.info("Step 3: Tracking quality metrics")
            quality_metrics = self.quality_monitor.track_confidence_distribution(batch_result)
            cycle_results['quality_metrics'] = self._serialize_quality_metrics(quality_metrics)
            
            # Step 4: AI analysis (if there are items needing review)
            if feedback_summary.needs_review > 0:
                logger.info("Step 4: Running AI analysis for improvement opportunities")
                ai_analysis = self._run_ai_analysis(batch_result, feedback_summary)
                cycle_results['ai_analysis'] = ai_analysis
                
                # Step 5: Generate rule suggestions
                if ai_analysis.get('patterns_found'):
                    logger.info("Step 5: Generating rule suggestions")
                    rule_suggestions = self._generate_rule_suggestions(ai_analysis)
                    cycle_results['rule_suggestions'] = rule_suggestions
                    
                    # Step 6: Submit rules for approval (auto-approve low-risk ones)
                    approved_rules = self._process_rule_suggestions(rule_suggestions)
                    cycle_results['approved_rules'] = approved_rules
            else:
                logger.info("No items need review - skipping AI analysis")
            
            # Step 7: Generate recommendations for next iteration
            logger.info("Step 7: Generating improvement recommendations")
            recommendations = self._generate_iteration_recommendations(cycle_results)
            cycle_results['recommendations'] = recommendations
            
            # Step 8: Create cycle summary
            cycle_summary = self._create_cycle_summary(cycle_results)
            cycle_results['cycle_summary'] = cycle_summary
            cycle_results['end_time'] = datetime.now().isoformat()
            
            # Save iteration results
            self._save_iteration_results(cycle_results)
            
            logger.info(f"Completed iterative cycle: {iteration_name}")
            logger.info(f"Cycle summary: {cycle_summary}")
            
            return cycle_results
            
        except Exception as e:
            logger.error(f"Error in iterative cycle {iteration_name}: {e}")
            cycle_results['error'] = str(e)
            cycle_results['end_time'] = datetime.now().isoformat()
            return cycle_results
    
    def _run_ai_analysis(self, batch_result, feedback_summary) -> Dict[str, Any]:
        """Run AI analysis on items that need review"""
        # Get items that need review
        review_items = [
            result for result in batch_result.results
            if result.confidence_level == "Low" or not result.success
        ]
        
        if not review_items:
            return {'patterns_found': False, 'analysis': 'No items need review'}
        
        # Analyze patterns
        pattern_analysis = self.pattern_analyzer.analyze_failure_patterns(review_items)
        
        # Aggregate analysis
        analysis_result = self.analysis_aggregator.aggregate_analysis([pattern_analysis])
        
        return {
            'patterns_found': True,
            'total_items_analyzed': len(review_items),
            'pattern_analysis': pattern_analysis,
            'aggregated_analysis': analysis_result,
            'improvement_opportunities': feedback_summary.improvement_opportunities
        }
    
    def _generate_rule_suggestions(self, ai_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate rule suggestions based on AI analysis"""
        try:
            # Extract patterns for rule generation
            patterns = ai_analysis.get('pattern_analysis', {}).get('patterns', [])
            
            rule_suggestions = []
            for pattern in patterns:
                suggestion = self.rule_suggester.suggest_rule_from_pattern(pattern)
                if suggestion:
                    rule_suggestions.append(suggestion)
            
            logger.info(f"Generated {len(rule_suggestions)} rule suggestions")
            return rule_suggestions
            
        except Exception as e:
            logger.error(f"Error generating rule suggestions: {e}")
            return []
    
    def _process_rule_suggestions(self, rule_suggestions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process rule suggestions through approval workflow"""
        approved_rules = []
        
        for suggestion in rule_suggestions:
            try:
                # Submit for approval
                approval_id = self.approval_workflow.submit_for_approval(suggestion)
                
                # Auto-approve low-risk rules
                if self._is_auto_approvable(suggestion):
                    success = self.approval_workflow.approve_rule(
                        approval_id,
                        "system_auto_approval",
                        "Auto-approved low-risk rule based on system analysis"
                    )
                    
                    if success:
                        approved_rules.append({
                            'suggestion': suggestion,
                            'approval_id': approval_id,
                            'status': 'auto_approved'
                        })
                        logger.info(f"Auto-approved rule: {suggestion.get('name', 'unnamed')}")
                else:
                    # Queue for manual review
                    approved_rules.append({
                        'suggestion': suggestion,
                        'approval_id': approval_id,
                        'status': 'pending_manual_review'
                    })
                    logger.info(f"Queued for manual review: {suggestion.get('name', 'unnamed')}")
                    
            except Exception as e:
                logger.error(f"Error processing rule suggestion: {e}")
                approved_rules.append({
                    'suggestion': suggestion,
                    'status': 'error',
                    'error': str(e)
                })
        
        return approved_rules
    
    def _is_auto_approvable(self, rule_suggestion: Dict[str, Any]) -> bool:
        """Determine if a rule suggestion can be auto-approved"""
        # Simple auto-approval criteria
        confidence = rule_suggestion.get('confidence', 0)
        rule_type = rule_suggestion.get('type', '')
        risk_level = rule_suggestion.get('risk_level', 'high')
        
        # Auto-approve high-confidence, low-risk rules
        return (confidence > 0.85 and 
                risk_level == 'low' and 
                rule_type in ['enhancement', 'feature_extraction', 'formatting'])
    
    def _generate_iteration_recommendations(self, cycle_results: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate recommendations for the next iteration"""
        recommendations = []
        
        # Get feedback summary
        feedback_summary = cycle_results.get('feedback_summary', {})
        batch_results = cycle_results.get('batch_results', {})
        quality_metrics = cycle_results.get('quality_metrics', {})
        
        # Analyze success rates
        success_rate = batch_results.get('summary', {}).get('success_rate', 0)
        high_confidence_rate = batch_results.get('summary', {}).get('high_confidence_rate', 0)
        
        # Batch size recommendations
        if high_confidence_rate > 0.9:
            recommendations.append({
                'type': 'batch_scaling',
                'priority': 'medium',
                'action': 'increase_batch_size',
                'message': f"High confidence rate ({high_confidence_rate:.1%}) - consider increasing batch size"
            })
        elif high_confidence_rate < 0.6:
            recommendations.append({
                'type': 'batch_scaling', 
                'priority': 'high',
                'action': 'focus_on_quality',
                'message': f"Low confidence rate ({high_confidence_rate:.1%}) - focus on quality improvements"
            })
        
        # Rule development recommendations
        needs_review = feedback_summary.get('needs_review', 0)
        if needs_review > batch_results.get('total_items', 0) * 0.3:
            recommendations.append({
                'type': 'rule_development',
                'priority': 'high',
                'action': 'develop_more_rules',
                'message': f"High review rate ({needs_review} items) - develop more rules"
            })
        
        # Quality monitoring recommendations
        quality_alerts = self.quality_monitor.detect_quality_alerts()
        for alert in quality_alerts:
            recommendations.append({
                'type': 'quality_alert',
                'priority': alert['severity'],
                'action': 'address_quality_issue',
                'message': alert['message']
            })
        
        # Get rule analyzer recommendations
        rule_recommendations = self.rule_analyzer.generate_improvement_recommendations()
        recommendations.extend(rule_recommendations)
        
        return recommendations
    
    def _create_cycle_summary(self, cycle_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create a comprehensive summary of the iteration cycle"""
        batch_results = cycle_results.get('batch_results', {})
        feedback_summary = cycle_results.get('feedback_summary', {})
        quality_metrics = cycle_results.get('quality_metrics', {})
        
        return {
            'iteration_info': {
                'name': cycle_results['iteration_name'],
                'number': cycle_results['iteration_number'],
                'duration': self._calculate_duration(cycle_results.get('start_time'), cycle_results.get('end_time'))
            },
            'batch_performance': {
                'total_items': batch_results.get('total_items', 0),
                'success_rate': batch_results.get('summary', {}).get('success_rate', 0),
                'high_confidence_rate': batch_results.get('summary', {}).get('high_confidence_rate', 0),
                'average_confidence': quality_metrics.get('average_confidence', 0)
            },
            'feedback_analysis': {
                'auto_accepted': feedback_summary.get('auto_accepted', 0),
                'needs_review': feedback_summary.get('needs_review', 0),
                'improvement_opportunities': len(feedback_summary.get('improvement_opportunities') or [])
            },
            'ai_contribution': {
                'analysis_performed': 'ai_analysis' in cycle_results,
                'rules_suggested': len(cycle_results.get('rule_suggestions') or []),
                'rules_approved': len([r for r in (cycle_results.get('approved_rules') or []) if r.get('status') == 'auto_approved'])
            },
            'quality_trend': {
                'current_confidence': quality_metrics.get('average_confidence', 0),
                'improvement_rate': quality_metrics.get('improvement_rate', 0)
            },
            'recommendations_count': len(cycle_results.get('recommendations', []))
        }
    
    def get_system_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive system dashboard"""
        return {
            'system_info': {
                'current_iteration': self.current_iteration,
                'total_batches_processed': len(self.batch_system.list_batches()),
                'last_updated': datetime.now().isoformat()
            },
            'quality_dashboard': self.quality_monitor.get_quality_dashboard(),
            'batch_performance': self.batch_system.get_recent_performance(days=14),
            'feedback_summary': self.feedback_manager.get_feedback_summary(days=14),
            'rule_management': {
                'total_rules': len(self.rule_manager.list_rules()),
                'pending_approvals': len(self.approval_workflow.get_pending_approvals()),
                'top_performing_rules': self.rule_analyzer.get_rule_effectiveness_ranking()[:5]
            },
            'improvement_trends': self.feedback_manager.get_improvement_trends(),
            'quality_alerts': self.quality_monitor.detect_quality_alerts()
        }
    
    def run_multiple_iterations(self, iterations: int, batch_configs: List[BatchConfig]) -> List[Dict[str, Any]]:
        """Run multiple iterative cycles"""
        iteration_results = []
        
        for i in range(iterations):
            # Use provided config or create default
            config = batch_configs[i] if i < len(batch_configs) else batch_configs[0]
            
            # Adjust batch size based on previous performance
            if i > 0:
                config = self._adjust_batch_config_based_on_performance(config, iteration_results[-1])
            
            # Run iteration
            result = self.run_iterative_cycle(config, f"iteration_{i+1}")
            iteration_results.append(result)
            
            # Check for critical issues that should stop iterations
            if self._should_stop_iterations(result):
                logger.warning(f"Stopping iterations after {i+1} due to critical issues")
                break
        
        return iteration_results
    
    def _adjust_batch_config_based_on_performance(self, base_config: BatchConfig, last_result: Dict[str, Any]) -> BatchConfig:
        """Adjust batch configuration based on previous performance"""
        # Simple batch size adjustment logic
        high_confidence_rate = last_result.get('cycle_summary', {}).get('batch_performance', {}).get('high_confidence_rate', 0)
        
        new_size = base_config.batch_size
        
        if high_confidence_rate > 0.9:
            # Increase batch size for high performance
            new_size = min(base_config.batch_size * 1.2, 100)
        elif high_confidence_rate < 0.6:
            # Decrease batch size for low performance
            new_size = max(base_config.batch_size * 0.8, 25)
        
        # Create new config with adjusted size
        adjusted_config = BatchConfig(
            batch_size=int(new_size),
            start_index=base_config.start_index,
            confidence_threshold_high=base_config.confidence_threshold_high,
            confidence_threshold_medium=base_config.confidence_threshold_medium,
            save_intermediate_results=base_config.save_intermediate_results,
            retry_failed_items=base_config.retry_failed_items
        )
        
        return adjusted_config
    
    def _should_stop_iterations(self, iteration_result: Dict[str, Any]) -> bool:
        """Determine if iterations should be stopped due to critical issues"""
        # Check for critical errors
        if 'error' in iteration_result:
            return True
        
        # Check for severely degraded performance
        success_rate = iteration_result.get('cycle_summary', {}).get('batch_performance', {}).get('success_rate', 1.0)
        if success_rate < 0.5:
            return True
        
        # Check for critical quality alerts
        quality_alerts = self.quality_monitor.detect_quality_alerts()
        critical_alerts = [alert for alert in quality_alerts if alert['severity'] == 'high']
        if len(critical_alerts) >= 3:
            return True
        
        return False
    
    def _serialize_batch_result(self, batch_result) -> Dict[str, Any]:
        """Convert BatchResult to serializable dict"""
        if not batch_result:
            return {}
            
        return {
            'batch_id': getattr(batch_result, 'batch_id', ''),
            'total_items': getattr(batch_result, 'total_items', 0),
            'successful_items': getattr(batch_result, 'successful_items', 0),
            'failed_items': getattr(batch_result, 'failed_items', 0),
            'processing_time': getattr(batch_result, 'processing_time', 0.0),
            'confidence_distribution': getattr(batch_result, 'confidence_distribution', {}),
            'summary': getattr(batch_result, 'summary', {})
        }
    
    def _serialize_feedback_summary(self, feedback_summary) -> Dict[str, Any]:
        """Convert FeedbackSummary to serializable dict"""
        return {
            'batch_id': feedback_summary.batch_id,
            'total_items': feedback_summary.total_items,
            'auto_accepted': feedback_summary.auto_accepted,
            'needs_review': feedback_summary.needs_review,
            'success_rate': feedback_summary.success_rate,
            'high_confidence_rate': feedback_summary.high_confidence_rate,
            'improvement_opportunities': feedback_summary.improvement_opportunities,
            'timestamp': feedback_summary.timestamp
        }
    
    def _serialize_quality_metrics(self, quality_metrics) -> Dict[str, Any]:
        """Convert QualityMetrics to serializable dict"""
        return {
            'timestamp': quality_metrics.timestamp,
            'batch_id': quality_metrics.batch_id,
            'total_items': quality_metrics.total_items,
            'confidence_distribution': quality_metrics.confidence_distribution,
            'average_confidence': quality_metrics.average_confidence,
            'success_rate': quality_metrics.success_rate,
            'high_confidence_rate': quality_metrics.high_confidence_rate,
            'processing_time_avg': quality_metrics.processing_time_avg,
            'improvement_rate': quality_metrics.improvement_rate
        }
    
    def _calculate_duration(self, start_time: str, end_time: str) -> float:
        """Calculate duration between two timestamps"""
        if not start_time or not end_time:
            return 0.0
        
        try:
            start = datetime.fromisoformat(start_time)
            end = datetime.fromisoformat(end_time)
            return (end - start).total_seconds()
        except:
            return 0.0
    
    def _save_iteration_results(self, cycle_results: Dict[str, Any]):
        """Save iteration results to file"""
        try:
            results_dir = self.data_dir / "iterations"
            results_dir.mkdir(exist_ok=True)
            
            iteration_file = results_dir / f"{cycle_results['iteration_name']}_results.json"
            
            with open(iteration_file, 'w', encoding='utf-8') as f:
                json.dump(cycle_results, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved iteration results to {iteration_file}")
            
        except Exception as e:
            logger.error(f"Error saving iteration results: {e}")
    
    def export_system_data(self, filepath: str):
        """Export comprehensive system data for analysis"""
        export_data = {
            'system_info': {
                'current_iteration': self.current_iteration,
                'export_timestamp': datetime.now().isoformat(),
                'total_batches': len(self.batch_system.list_batches())
            },
            'dashboard': self.get_system_dashboard(),
            'feedback_data': self.feedback_manager.get_feedback_summary(days=30),
            'quality_trends': self.quality_monitor.analyze_quality_trends(days=30),
            'rule_analysis': {
                'effectiveness_ranking': self.rule_analyzer.get_rule_effectiveness_ranking(),
                'underperforming_rules': self.rule_analyzer.get_underperforming_rules(),
                'improvement_recommendations': self.rule_analyzer.generate_improvement_recommendations()
            }
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported system data to {filepath}")
