# tests/test_ai_analysis.py
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from src.ai_analysis import AIClient, PatternAnalyzer, RuleSuggester, RuleSuggestion, AnalysisAggregator

class TestAIClient:
    """Test AI Client functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.mock_openai_client = Mock()
        self.ai_client = AIClient(api_key="test_key", model="gpt-4")
        self.ai_client.client = self.mock_openai_client
    
    def test_ai_client_initialization(self):
        """Test AI client initialization"""
        assert self.ai_client.api_key == "test_key"
        assert self.ai_client.model == "gpt-4"
    
    def test_ai_client_initialization_without_key(self):
        """Test AI client initialization without API key"""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="OpenAI API key is required"):
                AIClient()
    
    def test_analyze_failure_patterns(self):
        """Test failure pattern analysis"""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"patterns": ["test"], "missing_rules": ["company"]}'
        
        self.mock_openai_client.chat.completions.create.return_value = mock_response
        
        sample_results = [
            {
                'confidence_level': 'Low',
                'original_description': '36 C153 MJ 22 TN431 ZINC',
                'enhanced_description': '36-inch fitting',
                'extracted_features': {}
            }
        ]
        
        result = self.ai_client.analyze_failure_patterns(sample_results)
        
        assert 'patterns' in result
        assert result['patterns'] == ['test']
        self.mock_openai_client.chat.completions.create.assert_called_once()
    
    def test_analyze_failure_patterns_empty_input(self):
        """Test analysis with empty input"""
        result = self.ai_client.analyze_failure_patterns([])
        assert result['message'] == "No low-confidence results to analyze"
    
    def test_suggest_rules(self):
        """Test rule suggestion"""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '[{"rule_type": "company", "pattern": "TEST", "replacement": "Test Company"}]'
        
        self.mock_openai_client.chat.completions.create.return_value = mock_response
        
        failure_patterns = {"patterns": ["test"]}
        
        result = self.ai_client.suggest_rules(failure_patterns)
        
        assert len(result) == 1
        assert result[0]['rule_type'] == 'company'
        assert result[0]['pattern'] == 'TEST'
    
    def test_api_error_handling(self):
        """Test API error handling"""
        self.mock_openai_client.chat.completions.create.side_effect = Exception("API Error")
        
        result = self.ai_client.analyze_failure_patterns([{'confidence_level': 'Low'}])
        
        assert 'error' in result
        assert result['error'] == "API Error"


class TestPatternAnalyzer:
    """Test Pattern Analyzer functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.pattern_analyzer = PatternAnalyzer()
    
    def test_analyze_low_confidence_results(self):
        """Test low confidence results analysis"""
        sample_results = [
            {
                'confidence_level': 'Low',
                'original_description': 'SMITH BLAIR 36 C153 MJ 22 TN431 ZINC',
                'enhanced_description': '36-inch fitting',
                'extracted_features': {}
            },
            {
                'confidence_level': 'High',
                'original_description': 'Standard fitting',
                'enhanced_description': 'Standard pipe fitting',
                'extracted_features': {'company': 'Standard'}
            }
        ]
        
        analysis = self.pattern_analyzer.analyze_low_confidence_results(sample_results)
        
        assert 'total_low_confidence' in analysis
        assert analysis['total_low_confidence'] == 1
        assert 'common_patterns' in analysis
        assert 'missing_features' in analysis
        assert 'suggestions' in analysis
    
    def test_analyze_empty_results(self):
        """Test analysis with no low confidence results"""
        sample_results = [
            {
                'confidence_level': 'High',
                'original_description': 'Standard fitting',
                'enhanced_description': 'Standard pipe fitting',
                'extracted_features': {'company': 'Standard'}
            }
        ]
        
        analysis = self.pattern_analyzer.analyze_low_confidence_results(sample_results)
        
        assert analysis['message'] == "No low-confidence results to analyze"
    
    def test_find_common_patterns(self):
        """Test common pattern finding"""
        items = [
            {'original_description': 'SMITH BLAIR 36 C153'},
            {'original_description': 'SMITH 24 C110'}
        ]
        
        patterns = self.pattern_analyzer._find_common_patterns(items)
        
        assert 'common_words' in patterns
        assert 'SMITH' in patterns['common_words']
        assert patterns['common_words']['SMITH'] == 2
    
    def test_analyze_missing_features(self):
        """Test missing features analysis"""
        items = [
            {'extracted_features': {}},
            {'extracted_features': {'company': 'Smith'}},
            {'extracted_features': {}}
        ]
        
        missing = self.pattern_analyzer._analyze_missing_features(items)
        
        assert missing['company'] == 2  # Two items missing company
        assert missing.get('dimensions', 0) == 3  # All items missing dimensions
    
    def test_confidence_distribution_analysis(self):
        """Test confidence distribution analysis"""
        batch_results = [
            {'confidence_level': 'High'},
            {'confidence_level': 'Medium'},
            {'confidence_level': 'Low'},
            {'confidence_level': 'Low'}
        ]
        
        distribution = self.pattern_analyzer.analyze_confidence_distribution(batch_results)
        
        assert distribution['counts']['High'] == 1
        assert distribution['counts']['Medium'] == 1
        assert distribution['counts']['Low'] == 2
        assert distribution['percentages']['Low'] == 50.0


class TestRuleSuggester:
    """Test Rule Suggester functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.mock_ai_client = Mock()
        self.rule_suggester = RuleSuggester(self.mock_ai_client)
    
    def test_suggest_rules(self):
        """Test rule suggestion generation"""
        # Mock AI client response
        self.mock_ai_client.suggest_rules.return_value = [
            {
                'rule_type': 'company',
                'pattern': 'SMITH',
                'replacement': 'Smith Company',
                'confidence': 0.8,
                'reasoning': 'Common company name',
                'examples': ['SMITH BLAIR']
            }
        ]
        
        failure_analysis = {
            'suggestions': [
                {
                    'type': 'specification',
                    'pattern': 'C153',
                    'replacement': 'AWWA C153',
                    'confidence': 0.9,
                    'reasoning': 'Standard specification'
                }
            ]
        }
        
        suggestions = self.rule_suggester.suggest_rules(failure_analysis)
        
        assert len(suggestions) >= 1
        assert any(s.rule_type == 'company' for s in suggestions)
        assert any(s.rule_type == 'specification' for s in suggestions)
    
    def test_rule_suggestion_validation(self):
        """Test rule suggestion validation"""
        valid_suggestion = RuleSuggestion(
            rule_type='company',
            pattern='SMITH',
            replacement='Smith Company',
            confidence=0.8,
            reasoning='Test reasoning',
            examples=['SMITH BLAIR']
        )
        
        validation = self.rule_suggester.validate_suggestion(valid_suggestion)
        
        assert validation['valid'] == True
        assert len(validation['issues']) == 0
    
    def test_invalid_rule_suggestion(self):
        """Test invalid rule suggestion validation"""
        invalid_suggestion = RuleSuggestion(
            rule_type='company',
            pattern='',  # Empty pattern
            replacement='',  # Empty replacement
            confidence=0.8,
            reasoning='Test reasoning',
            examples=[]
        )
        
        validation = self.rule_suggester.validate_suggestion(invalid_suggestion)
        
        assert validation['valid'] == False
        assert 'Empty pattern' in validation['issues']
        assert 'Empty replacement' in validation['issues']
    
    def test_filter_suggestions(self):
        """Test suggestion filtering"""
        suggestions = [
            RuleSuggestion('company', 'SMITH', 'Smith', 0.9, 'Good', []),
            RuleSuggestion('company', '', 'Invalid', 0.8, 'Bad', []),  # Invalid
            RuleSuggestion('company', 'TEST', 'Test', 0.2, 'Low conf', [])  # Low confidence
        ]
        
        filtered = self.rule_suggester.filter_suggestions(suggestions, min_confidence=0.5)
        
        assert len(filtered) == 1
        assert filtered[0].pattern == 'SMITH'
    
    def test_categorize_abbreviation(self):
        """Test abbreviation categorization"""
        assert self.rule_suggester._categorize_abbreviation('DI') == 'material'
        assert self.rule_suggester._categorize_abbreviation('MJ') == 'connection_type'
        assert self.rule_suggester._categorize_abbreviation('C153') == 'specification'
        assert self.rule_suggester._categorize_abbreviation('TEE') == 'product_type'


class TestAnalysisAggregator:
    """Test Analysis Aggregator functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.mock_ai_client = Mock()
        self.test_data_dir = Path("/tmp/test_data")
        self.analysis_aggregator = AnalysisAggregator(self.mock_ai_client, self.test_data_dir)
    
    def test_batch_summary_creation(self):
        """Test batch summary creation"""
        batch_results = [
            {'confidence_level': 'High', 'success': True},
            {'confidence_level': 'Medium', 'success': True},
            {'confidence_level': 'Low', 'success': False},
            {'confidence_level': 'Low', 'success': False}
        ]
        
        summary = self.analysis_aggregator._create_batch_summary(batch_results)
        
        assert summary['total_items'] == 4
        assert summary['confidence_distribution']['High'] == 1
        assert summary['confidence_distribution']['Low'] == 2
        assert summary['success_rate'] == 0.5
        assert summary['confidence_percentages']['Low'] == 50.0
    
    def test_rule_suggestion_to_dict(self):
        """Test rule suggestion to dictionary conversion"""
        suggestion = RuleSuggestion(
            rule_type='company',
            pattern='SMITH',
            replacement='Smith Company',
            confidence=0.8,
            reasoning='Test',
            examples=['example'],
            priority=2
        )
        
        result_dict = self.analysis_aggregator._rule_suggestion_to_dict(suggestion)
        
        assert result_dict['rule_type'] == 'company'
        assert result_dict['pattern'] == 'SMITH'
        assert result_dict['confidence'] == 0.8
        assert result_dict['priority'] == 2
    
    def test_insights_generation(self):
        """Test insights generation"""
        pattern_analysis = {
            'missing_features': {'company': 10, 'specification': 5},
            'total_low_confidence': 15
        }
        
        rule_suggestions = [
            Mock(confidence=0.9, rule_type='company'),
            Mock(confidence=0.7, rule_type='specification'),
            Mock(confidence=0.6, rule_type='material')
        ]
        
        insights = self.analysis_aggregator._generate_insights(pattern_analysis, rule_suggestions)
        
        assert len(insights) > 0
        assert any('Most missing feature: company' in insight for insight in insights)
        assert any('Generated 3 rule suggestions' in insight for insight in insights)
    
    @patch('builtins.open', create=True)
    @patch('json.dump')
    def test_save_analysis(self, mock_json_dump, mock_open):
        """Test analysis saving"""
        analysis = {'test': 'data'}
        
        self.analysis_aggregator._save_analysis(analysis)
        
        mock_open.assert_called_once()
        mock_json_dump.assert_called_once()


class TestAIAnalysisIntegration:
    """Test AI Analysis integration"""
    
    def test_full_analysis_pipeline(self):
        """Test complete analysis pipeline"""
        # Mock AI client
        mock_ai_client = Mock()
        mock_ai_client.suggest_rules.return_value = [
            {
                'rule_type': 'company',
                'pattern': 'SMITH',
                'replacement': 'Smith Company',
                'confidence': 0.8,
                'reasoning': 'Common company name',
                'examples': []
            }
        ]
        
        # Create aggregator
        test_data_dir = Path("/tmp/test")
        aggregator = AnalysisAggregator(mock_ai_client, test_data_dir)
        
        # Sample batch results
        batch_results = [
            {
                'confidence_level': 'Low',
                'original_description': 'SMITH BLAIR 36 C153',
                'enhanced_description': '36-inch fitting',
                'extracted_features': {},
                'success': False
            },
            {
                'confidence_level': 'High',
                'original_description': 'Standard fitting',
                'enhanced_description': 'Standard pipe fitting',
                'extracted_features': {'company': 'Standard'},
                'success': True
            }
        ]
        
        # Run analysis
        with patch.object(aggregator, '_save_analysis'):
            analysis = aggregator.analyze_batch_results(batch_results)
        
        # Verify results
        assert 'batch_summary' in analysis
        assert 'pattern_analysis' in analysis
        assert 'rule_suggestions' in analysis
        assert 'insights' in analysis
        assert 'recommendations' in analysis
        
        assert analysis['batch_summary']['total_items'] == 2
        assert len(analysis['rule_suggestions']) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
