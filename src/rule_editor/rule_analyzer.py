# src/rule_editor/rule_analyzer.py
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
from pathlib import Path
import statistics

try:
    from batch_processor.processor import BatchResult, ProcessingResult
    from batch_processor.feedback_loop import FeedbackItem
    from utils.logger import get_logger
except ImportError:
    # Fallback for when running as script
    from batch_processor.processor import BatchResult, ProcessingResult  
    from batch_processor.feedback_loop import FeedbackItem
    from utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class RuleImpact:
    """Impact analysis of a specific rule"""
    rule_id: str
    rule_name: str
    implementation_date: str
    before_metrics: Dict[str, float]
    after_metrics: Dict[str, float]
    improvement: float
    effectiveness: float
    items_affected: int
    confidence_change: float
    success_rate_change: float
    significance: str  # 'high', 'medium', 'low', 'negligible'

@dataclass
class RulePerformance:
    """Performance tracking for a rule over time"""
    rule_id: str
    rule_name: str
    creation_date: str
    total_applications: int
    successful_applications: int
    failed_applications: int
    average_improvement: float
    confidence_impact: float
    recent_performance: Dict[str, Any]

class RuleImpactAnalyzer:
    """Analyzes the effectiveness of rules on system performance"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.analysis_dir = self.data_dir / "analysis" 
        self.analysis_dir.mkdir(exist_ok=True)
        
        self.rule_impacts: Dict[str, RuleImpact] = {}
        self.rule_performance: Dict[str, RulePerformance] = {}
        
        # Load existing analysis data
        self._load_analysis_history()
    
    def analyze_rule_effectiveness(self, rule_id: str, before_after_data: Dict) -> RuleImpact:
        """Analyze the impact of a specific rule on confidence scores"""
        logger.info(f"Analyzing effectiveness of rule {rule_id}")
        
        before_data = before_after_data.get("before", {})
        after_data = before_after_data.get("after", {})
        
        # Extract metrics
        before_metrics = self._extract_metrics(before_data)
        after_metrics = self._extract_metrics(after_data)
        
        # Calculate improvements
        confidence_change = after_metrics['avg_confidence'] - before_metrics['avg_confidence']
        success_rate_change = after_metrics['success_rate'] - before_metrics['success_rate']
        
        # Calculate overall improvement (weighted average)
        improvement = (confidence_change * 0.7) + (success_rate_change * 0.3)
        
        # Calculate effectiveness based on improvement and sample size
        items_affected = after_metrics.get('total_items', 0)
        effectiveness = self._calculate_effectiveness(improvement, items_affected)
        
        # Determine significance
        significance = self._determine_significance(improvement, items_affected, confidence_change)
        
        # Get rule info
        rule_info = before_after_data.get("rule_info", {})
        rule_name = rule_info.get("name", f"Rule {rule_id}")
        implementation_date = rule_info.get("implementation_date", datetime.now().isoformat())
        
        # Create impact analysis
        impact = RuleImpact(
            rule_id=rule_id,
            rule_name=rule_name,
            implementation_date=implementation_date,
            before_metrics=before_metrics,
            after_metrics=after_metrics,
            improvement=round(improvement, 4),
            effectiveness=round(effectiveness, 4),
            items_affected=items_affected,
            confidence_change=round(confidence_change, 4),
            success_rate_change=round(success_rate_change, 4),
            significance=significance
        )
        
        # Store impact analysis
        self.rule_impacts[rule_id] = impact
        
        # Save analysis
        self._save_rule_impact(impact)
        
        logger.info(f"Rule {rule_id} analysis: {improvement:.4f} improvement, {significance} significance")
        
        return impact
    
    def _extract_metrics(self, data: Dict) -> Dict[str, float]:
        """Extract key metrics from batch data"""
        if not data:
            return {
                'avg_confidence': 0.0,
                'success_rate': 0.0,
                'high_confidence_rate': 0.0,
                'total_items': 0
            }
        
        # Handle different data formats
        if 'results' in data:  # BatchResult format
            results = data['results']
            successful_results = [r for r in results if r.get('success', False)]
            
            confidence_scores = [r.get('confidence_score', 0) for r in successful_results]
            avg_confidence = statistics.mean(confidence_scores) if confidence_scores else 0.0
            
            success_rate = len(successful_results) / len(results) if results else 0.0
            
            high_confidence_count = sum(1 for r in results if r.get('confidence_level') == 'High')
            high_confidence_rate = high_confidence_count / len(results) if results else 0.0
            
            return {
                'avg_confidence': avg_confidence,
                'success_rate': success_rate,
                'high_confidence_rate': high_confidence_rate,
                'total_items': len(results)
            }
        
        elif 'confidence_scores' in data:  # Direct metrics format
            return {
                'avg_confidence': statistics.mean(data['confidence_scores']) if data['confidence_scores'] else 0.0,
                'success_rate': data.get('success_rate', 0.0),
                'high_confidence_rate': data.get('high_confidence_rate', 0.0),
                'total_items': data.get('total_items', 0)
            }
        
        else:  # Summary format
            return {
                'avg_confidence': data.get('avg_confidence', 0.0),
                'success_rate': data.get('success_rate', 0.0),
                'high_confidence_rate': data.get('high_confidence_rate', 0.0),
                'total_items': data.get('total_items', 0)
            }
    
    def _calculate_effectiveness(self, improvement: float, sample_size: int) -> float:
        """Calculate rule effectiveness based on improvement and sample size"""
        if sample_size == 0:
            return 0.0
        
        # Base effectiveness from improvement
        base_effectiveness = max(0, min(1, improvement + 0.5))  # Normalize around 0.5
        
        # Adjust for sample size confidence
        size_confidence = min(1.0, sample_size / 50.0)  # Full confidence at 50+ items
        
        return base_effectiveness * size_confidence
    
    def _determine_significance(self, improvement: float, sample_size: int, confidence_change: float) -> str:
        """Determine the statistical significance of the rule impact"""
        if sample_size < 10:
            return "negligible"  # Too small sample size
        
        if abs(improvement) < 0.01:
            return "negligible"  # Very small improvement
        
        if improvement > 0.1 and confidence_change > 0.05:
            return "high"
        elif improvement > 0.05 or abs(confidence_change) > 0.03:
            return "medium"
        elif improvement > 0.01:
            return "low"
        else:
            return "negligible"
    
    def track_rule_performance(self, rule_id: str, application_result: Dict):
        """Track ongoing performance of a rule"""
        if rule_id not in self.rule_performance:
            # Initialize performance tracking
            self.rule_performance[rule_id] = RulePerformance(
                rule_id=rule_id,
                rule_name=application_result.get('rule_name', f'Rule {rule_id}'),
                creation_date=application_result.get('creation_date', datetime.now().isoformat()),
                total_applications=0,
                successful_applications=0,
                failed_applications=0,
                average_improvement=0.0,
                confidence_impact=0.0,
                recent_performance={}
            )
        
        performance = self.rule_performance[rule_id]
        
        # Update application counts
        performance.total_applications += 1
        
        if application_result.get('success', False):
            performance.successful_applications += 1
            
            # Update improvement metrics
            improvement = application_result.get('improvement', 0.0)
            current_avg = performance.average_improvement
            n = performance.successful_applications
            
            # Running average update
            performance.average_improvement = ((current_avg * (n-1)) + improvement) / n
            
            # Update confidence impact
            confidence_impact = application_result.get('confidence_impact', 0.0)
            performance.confidence_impact = ((performance.confidence_impact * (n-1)) + confidence_impact) / n
        else:
            performance.failed_applications += 1
        
        # Update recent performance (last 30 days)
        self._update_recent_performance(performance, application_result)
        
        # Save performance data
        self._save_rule_performance(performance)
    
    def _update_recent_performance(self, performance: RulePerformance, application_result: Dict):
        """Update recent performance metrics"""
        today = datetime.now().date().isoformat()
        
        if 'daily_stats' not in performance.recent_performance:
            performance.recent_performance['daily_stats'] = {}
        
        daily_stats = performance.recent_performance['daily_stats']
        
        if today not in daily_stats:
            daily_stats[today] = {
                'applications': 0,
                'successes': 0,
                'total_improvement': 0.0,
                'confidence_impacts': []
            }
        
        today_stats = daily_stats[today]
        today_stats['applications'] += 1
        
        if application_result.get('success', False):
            today_stats['successes'] += 1
            today_stats['total_improvement'] += application_result.get('improvement', 0.0)
            today_stats['confidence_impacts'].append(application_result.get('confidence_impact', 0.0))
        
        # Keep only last 30 days
        cutoff_date = (datetime.now() - timedelta(days=30)).date().isoformat()
        daily_stats = {
            date: stats for date, stats in daily_stats.items() 
            if date >= cutoff_date
        }
        performance.recent_performance['daily_stats'] = daily_stats
    
    def get_rule_effectiveness_ranking(self, min_applications: int = 10) -> List[Tuple[str, float]]:
        """Get rules ranked by effectiveness"""
        effective_rules = []
        
        for rule_id, performance in self.rule_performance.items():
            if performance.total_applications >= min_applications:
                # Calculate composite effectiveness score
                success_rate = performance.successful_applications / performance.total_applications
                effectiveness_score = (
                    performance.average_improvement * 0.4 +
                    success_rate * 0.3 + 
                    abs(performance.confidence_impact) * 0.3
                )
                effective_rules.append((rule_id, effectiveness_score))
        
        # Sort by effectiveness (descending)
        effective_rules.sort(key=lambda x: x[1], reverse=True)
        
        return effective_rules
    
    def get_underperforming_rules(self, threshold: float = 0.01) -> List[str]:
        """Identify rules that are underperforming"""
        underperforming = []
        
        for rule_id, performance in self.rule_performance.items():
            if performance.total_applications >= 5:  # Minimum applications to evaluate
                success_rate = performance.successful_applications / performance.total_applications
                
                # Consider underperforming if:
                # - Low success rate OR
                # - Negative average improvement OR  
                # - Very small positive improvement
                if (success_rate < 0.7 or 
                    performance.average_improvement < 0 or
                    (0 <= performance.average_improvement < threshold)):
                    underperforming.append(rule_id)
        
        return underperforming
    
    def analyze_rule_interactions(self, rule_combinations: List[List[str]]) -> Dict[str, Any]:
        """Analyze how rules interact when applied together"""
        interaction_analysis = {}
        
        for combination in rule_combinations:
            combination_key = "+".join(sorted(combination))
            
            # Find batches where this combination was applied
            combination_impacts = []
            
            for rule_id in combination:
                if rule_id in self.rule_impacts:
                    combination_impacts.append(self.rule_impacts[rule_id])
            
            if len(combination_impacts) >= 2:
                # Calculate synergy effects
                individual_improvements = [impact.improvement for impact in combination_impacts]
                expected_combined = sum(individual_improvements)
                
                # This is a simplified analysis - in practice you'd need actual combined data
                interaction_analysis[combination_key] = {
                    'rules': combination,
                    'individual_improvements': individual_improvements,
                    'expected_combined': expected_combined,
                    'synergy_potential': 'medium'  # Would calculate based on actual data
                }
        
        return interaction_analysis
    
    def get_rule_impact_summary(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive impact summary for a rule"""
        if rule_id not in self.rule_impacts:
            return None
        
        impact = self.rule_impacts[rule_id]
        performance = self.rule_performance.get(rule_id)
        
        summary = {
            'rule_info': {
                'id': impact.rule_id,
                'name': impact.rule_name,
                'implementation_date': impact.implementation_date
            },
            'impact_analysis': {
                'improvement': impact.improvement,
                'effectiveness': impact.effectiveness,
                'significance': impact.significance,
                'items_affected': impact.items_affected,
                'confidence_change': impact.confidence_change,
                'success_rate_change': impact.success_rate_change
            },
            'before_after_comparison': {
                'before': impact.before_metrics,
                'after': impact.after_metrics
            }
        }
        
        if performance:
            summary['ongoing_performance'] = {
                'total_applications': performance.total_applications,
                'success_rate': performance.successful_applications / performance.total_applications if performance.total_applications > 0 else 0,
                'average_improvement': performance.average_improvement,
                'confidence_impact': performance.confidence_impact,
                'recent_activity': len(performance.recent_performance.get('daily_stats', {}))
            }
        
        return summary
    
    def generate_improvement_recommendations(self) -> List[Dict[str, str]]:
        """Generate recommendations for rule improvements"""
        recommendations = []
        
        # Identify underperforming rules
        underperforming = self.get_underperforming_rules()
        if underperforming:
            recommendations.append({
                'type': 'rule_removal',
                'priority': 'high',
                'message': f"Consider reviewing or removing {len(underperforming)} underperforming rules",
                'rules': underperforming
            })
        
        # Identify highly effective rules that could be expanded
        top_rules = self.get_rule_effectiveness_ranking()[:3]
        if top_rules:
            recommendations.append({
                'type': 'rule_expansion',
                'priority': 'medium', 
                'message': "Consider creating similar rules based on top performers",
                'rules': [rule_id for rule_id, _ in top_rules]
            })
        
        # Check for rules with limited data
        limited_data_rules = [
            rule_id for rule_id, performance in self.rule_performance.items()
            if performance.total_applications < 10
        ]
        
        if limited_data_rules:
            recommendations.append({
                'type': 'data_collection',
                'priority': 'low',
                'message': f"Need more data to evaluate {len(limited_data_rules)} rules",
                'rules': limited_data_rules
            })
        
        return recommendations
    
    def _save_rule_impact(self, impact: RuleImpact):
        """Save rule impact analysis to file"""
        try:
            impact_file = self.analysis_dir / f"rule_impact_{impact.rule_id}.json"
            
            data = {
                'rule_id': impact.rule_id,
                'rule_name': impact.rule_name,
                'implementation_date': impact.implementation_date,
                'before_metrics': impact.before_metrics,
                'after_metrics': impact.after_metrics,
                'improvement': impact.improvement,
                'effectiveness': impact.effectiveness,
                'items_affected': impact.items_affected,
                'confidence_change': impact.confidence_change,
                'success_rate_change': impact.success_rate_change,
                'significance': impact.significance,
                'analysis_date': datetime.now().isoformat()
            }
            
            with open(impact_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Error saving rule impact analysis: {e}")
    
    def _save_rule_performance(self, performance: RulePerformance):
        """Save rule performance data to file"""
        try:
            performance_file = self.analysis_dir / f"rule_performance_{performance.rule_id}.json"
            
            data = {
                'rule_id': performance.rule_id,
                'rule_name': performance.rule_name,
                'creation_date': performance.creation_date,
                'total_applications': performance.total_applications,
                'successful_applications': performance.successful_applications,
                'failed_applications': performance.failed_applications,
                'average_improvement': performance.average_improvement,
                'confidence_impact': performance.confidence_impact,
                'recent_performance': performance.recent_performance,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(performance_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Error saving rule performance data: {e}")
    
    def _load_analysis_history(self):
        """Load existing rule analysis data"""
        try:
            # Load impact analyses
            impact_files = list(self.analysis_dir.glob("rule_impact_*.json"))
            for impact_file in impact_files:
                with open(impact_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                impact = RuleImpact(
                    rule_id=data['rule_id'],
                    rule_name=data['rule_name'],
                    implementation_date=data['implementation_date'],
                    before_metrics=data['before_metrics'],
                    after_metrics=data['after_metrics'],
                    improvement=data['improvement'],
                    effectiveness=data['effectiveness'],
                    items_affected=data['items_affected'],
                    confidence_change=data['confidence_change'],
                    success_rate_change=data['success_rate_change'],
                    significance=data['significance']
                )
                
                self.rule_impacts[data['rule_id']] = impact
            
            # Load performance data
            performance_files = list(self.analysis_dir.glob("rule_performance_*.json"))
            for performance_file in performance_files:
                with open(performance_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                performance = RulePerformance(
                    rule_id=data['rule_id'],
                    rule_name=data['rule_name'],
                    creation_date=data['creation_date'],
                    total_applications=data['total_applications'],
                    successful_applications=data['successful_applications'],
                    failed_applications=data['failed_applications'],
                    average_improvement=data['average_improvement'],
                    confidence_impact=data['confidence_impact'],
                    recent_performance=data.get('recent_performance', {})
                )
                
                self.rule_performance[data['rule_id']] = performance
            
            logger.info(f"Loaded analysis data for {len(self.rule_impacts)} rule impacts and {len(self.rule_performance)} rule performances")
            
        except Exception as e:
            logger.error(f"Error loading analysis history: {e}")
    
    def export_analysis_data(self, filepath: str):
        """Export all rule analysis data"""
        export_data = {
            'rule_impacts': {
                rule_id: {
                    'rule_id': impact.rule_id,
                    'rule_name': impact.rule_name,
                    'implementation_date': impact.implementation_date,
                    'before_metrics': impact.before_metrics,
                    'after_metrics': impact.after_metrics,
                    'improvement': impact.improvement,
                    'effectiveness': impact.effectiveness,
                    'items_affected': impact.items_affected,
                    'confidence_change': impact.confidence_change,
                    'success_rate_change': impact.success_rate_change,
                    'significance': impact.significance
                }
                for rule_id, impact in self.rule_impacts.items()
            },
            'rule_performance': {
                rule_id: {
                    'rule_id': performance.rule_id,
                    'rule_name': performance.rule_name,
                    'creation_date': performance.creation_date,
                    'total_applications': performance.total_applications,
                    'successful_applications': performance.successful_applications,
                    'failed_applications': performance.failed_applications,
                    'average_improvement': performance.average_improvement,
                    'confidence_impact': performance.confidence_impact,
                    'recent_performance': performance.recent_performance
                }
                for rule_id, performance in self.rule_performance.items()
            },
            'exported_at': datetime.now().isoformat()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported rule analysis data to {filepath}")

