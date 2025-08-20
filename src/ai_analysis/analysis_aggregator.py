# src/ai_analysis/analysis_aggregator.py
from typing import Dict, List
from datetime import datetime
import json
from pathlib import Path

from .pattern_analyzer import PatternAnalyzer
from .rule_suggester import RuleSuggester
from ..utils.logger import get_logger

logger = get_logger(__name__)

class AnalysisAggregator:
    """Aggregates analysis results and generates insights"""
    
    def __init__(self, ai_client, data_dir: Path):
        self.pattern_analyzer = PatternAnalyzer()
        self.rule_suggester = RuleSuggester(ai_client)
        self.data_dir = data_dir
        self.analysis_dir = data_dir / "analysis"
        self.analysis_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logger
    
    def analyze_batch_results(self, batch_results: List[Dict]) -> Dict:
        """Complete analysis of batch results"""
        self.logger.info(f"Starting analysis of {len(batch_results)} batch results")
        
        # Analyze low-confidence results
        pattern_analysis = self.pattern_analyzer.analyze_low_confidence_results(batch_results)
        
        # Generate rule suggestions
        rule_suggestions = self.rule_suggester.suggest_rules(pattern_analysis)
        
        # Filter and rank suggestions
        filtered_suggestions = self.rule_suggester.filter_suggestions(rule_suggestions)
        ranked_suggestions = self.rule_suggester.rank_suggestions(filtered_suggestions)
        
        # Create comprehensive analysis
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'batch_summary': self._create_batch_summary(batch_results),
            'pattern_analysis': pattern_analysis,
            'rule_suggestions': [self._rule_suggestion_to_dict(s) for s in ranked_suggestions],
            'insights': self._generate_insights(pattern_analysis, ranked_suggestions),
            'recommendations': self._generate_recommendations(ranked_suggestions),
            'metadata': {
                'total_suggestions': len(rule_suggestions),
                'filtered_suggestions': len(filtered_suggestions),
                'high_priority_suggestions': len([s for s in ranked_suggestions if s.priority >= 3])
            }
        }
        
        # Save analysis
        self._save_analysis(analysis)
        
        self.logger.info(f"Analysis completed with {len(ranked_suggestions)} recommendations")
        return analysis
    
    def _create_batch_summary(self, results: List[Dict]) -> Dict:
        """Create summary of batch results"""
        total_items = len(results)
        confidence_distribution = {'High': 0, 'Medium': 0, 'Low': 0}
        success_count = 0
        
        for result in results:
            confidence_level = result.get('confidence_level', 'Low')
            confidence_distribution[confidence_level] += 1
            
            if result.get('success', False):
                success_count += 1
        
        return {
            'total_items': total_items,
            'confidence_distribution': confidence_distribution,
            'success_rate': success_count / total_items if total_items > 0 else 0,
            'confidence_percentages': {
                level: (count / total_items * 100) if total_items > 0 else 0
                for level, count in confidence_distribution.items()
            }
        }
    
    def _rule_suggestion_to_dict(self, suggestion) -> Dict:
        """Convert RuleSuggestion to dictionary"""
        result = {
            'rule_type': suggestion.rule_type,
            'pattern': suggestion.pattern,
            'replacement': suggestion.replacement,
            'confidence': suggestion.confidence,
            'reasoning': suggestion.reasoning,
            'examples': suggestion.examples,
            'priority': suggestion.priority
        }
        
        # Add composite score if it exists
        if hasattr(suggestion, 'composite_score'):
            result['composite_score'] = suggestion.composite_score
        
        return result
    
    def _generate_insights(self, pattern_analysis: Dict, rule_suggestions: List) -> List[str]:
        """Generate insights from analysis"""
        insights = []
        
        # Pattern insights
        if pattern_analysis.get('missing_features'):
            missing = pattern_analysis['missing_features']
            most_missing = max(missing.items(), key=lambda x: x[1]) if missing else None
            if most_missing:
                insights.append(f"Most missing feature: {most_missing[0]} ({most_missing[1]} items)")
        
        # Rule suggestion insights
        if rule_suggestions:
            high_confidence = [s for s in rule_suggestions if s.confidence > 0.8]
            insights.append(f"Generated {len(rule_suggestions)} rule suggestions ({len(high_confidence)} high confidence)")
            
            # Rule type distribution
            rule_types = {}
            for suggestion in rule_suggestions:
                rule_types[suggestion.rule_type] = rule_types.get(suggestion.rule_type, 0) + 1
            
            most_common_type = max(rule_types.items(), key=lambda x: x[1]) if rule_types else None
            if most_common_type:
                insights.append(f"Most common suggestion type: {most_common_type[0]} ({most_common_type[1]} suggestions)")
        
        # Context issues insights
        context_issues = pattern_analysis.get('context_issues', [])
        if context_issues:
            issue_types = {}
            for issue in context_issues:
                issue_type = issue.get('type', 'unknown')
                issue_types[issue_type] = issue_types.get(issue_type, 0) + 1
            
            insights.append(f"Found {len(context_issues)} context interpretation issues")
            if issue_types:
                most_common_issue = max(issue_types.items(), key=lambda x: x[1])
                insights.append(f"Most common issue: {most_common_issue[0]} ({most_common_issue[1]} occurrences)")
        
        # Low confidence rate insight
        total_low_confidence = pattern_analysis.get('total_low_confidence', 0)
        if total_low_confidence > 0:
            insights.append(f"Low confidence rate suggests need for rule improvements")
        
        return insights
    
    def _generate_recommendations(self, rule_suggestions: List) -> List[Dict]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # High priority recommendations
        high_priority = [s for s in rule_suggestions if s.priority >= 3]
        if high_priority:
            recommendations.append({
                'type': 'high_priority_rules',
                'description': f"Consider implementing {len(high_priority)} high-priority rules",
                'priority': 'high',
                'rules': [self._rule_suggestion_to_dict(s) for s in high_priority[:3]]
            })
        
        # Company name recommendations
        company_rules = [s for s in rule_suggestions if s.rule_type == 'company']
        if company_rules:
            recommendations.append({
                'type': 'company_rules',
                'description': f"Add {len(company_rules)} company name recognition rules",
                'priority': 'medium',
                'rules': [self._rule_suggestion_to_dict(s) for s in company_rules[:3]]
            })
        
        # Specification recommendations
        spec_rules = [s for s in rule_suggestions if s.rule_type == 'specification']
        if spec_rules:
            recommendations.append({
                'type': 'specification_rules',
                'description': f"Add {len(spec_rules)} specification recognition rules",
                'priority': 'medium',
                'rules': [self._rule_suggestion_to_dict(s) for s in spec_rules[:3]]
            })
        
        # Material recommendations
        material_rules = [s for s in rule_suggestions if s.rule_type == 'material']
        if material_rules:
            recommendations.append({
                'type': 'material_rules',
                'description': f"Add {len(material_rules)} material recognition rules",
                'priority': 'low',
                'rules': [self._rule_suggestion_to_dict(s) for s in material_rules[:3]]
            })
        
        # High confidence recommendations
        high_confidence_rules = [s for s in rule_suggestions if s.confidence > 0.8]
        if high_confidence_rules:
            recommendations.append({
                'type': 'high_confidence_rules',
                'description': f"Implement {len(high_confidence_rules)} high-confidence rules immediately",
                'priority': 'high',
                'rules': [self._rule_suggestion_to_dict(s) for s in high_confidence_rules[:5]]
            })
        
        return recommendations
    
    def _save_analysis(self, analysis: Dict):
        """Save analysis to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        analysis_file = self.analysis_dir / f"analysis_{timestamp}.json"
        
        try:
            with open(analysis_file, 'w') as f:
                json.dump(analysis, f, indent=2, default=str)
            
            self.logger.info(f"Analysis saved to {analysis_file}")
        except Exception as e:
            self.logger.error(f"Failed to save analysis: {e}")
    
    def load_previous_analysis(self, analysis_file: str = None) -> Dict:
        """Load a previous analysis from file"""
        if analysis_file:
            analysis_path = self.analysis_dir / analysis_file
        else:
            # Get most recent analysis
            analysis_files = list(self.analysis_dir.glob("analysis_*.json"))
            if not analysis_files:
                return {}
            analysis_path = max(analysis_files, key=lambda x: x.stat().st_mtime)
        
        try:
            with open(analysis_path, 'r') as f:
                analysis = json.load(f)
            self.logger.info(f"Loaded analysis from {analysis_path}")
            return analysis
        except Exception as e:
            self.logger.error(f"Failed to load analysis: {e}")
            return {}
    
    def compare_analyses(self, current_analysis: Dict, previous_analysis: Dict) -> Dict:
        """Compare current analysis with previous analysis"""
        comparison = {
            'timestamp': datetime.now().isoformat(),
            'improvement_metrics': {},
            'changes': [],
            'trends': []
        }
        
        # Compare success rates
        current_success = current_analysis.get('batch_summary', {}).get('success_rate', 0)
        previous_success = previous_analysis.get('batch_summary', {}).get('success_rate', 0)
        
        comparison['improvement_metrics']['success_rate_change'] = current_success - previous_success
        
        # Compare confidence distributions
        current_confidence = current_analysis.get('batch_summary', {}).get('confidence_distribution', {})
        previous_confidence = previous_analysis.get('batch_summary', {}).get('confidence_distribution', {})
        
        for level in ['High', 'Medium', 'Low']:
            current_count = current_confidence.get(level, 0)
            previous_count = previous_confidence.get(level, 0)
            comparison['improvement_metrics'][f'{level.lower()}_confidence_change'] = current_count - previous_count
        
        # Compare number of suggestions
        current_suggestions = len(current_analysis.get('rule_suggestions', []))
        previous_suggestions = len(previous_analysis.get('rule_suggestions', []))
        
        comparison['improvement_metrics']['suggestions_change'] = current_suggestions - previous_suggestions
        
        # Generate trend insights
        if comparison['improvement_metrics']['success_rate_change'] > 0.05:
            comparison['trends'].append("Success rate is improving")
        elif comparison['improvement_metrics']['success_rate_change'] < -0.05:
            comparison['trends'].append("Success rate is declining")
        
        if comparison['improvement_metrics']['high_confidence_change'] > 0:
            comparison['trends'].append("More high-confidence results")
        
        return comparison
