# src/ai_analysis/ai_client.py
import openai
import os
from typing import Dict, List, Optional
import json
import re
from utils.logger import get_logger

logger = get_logger(__name__)

class AIClient:
    """Manages OpenAI API interactions"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
        
        self.client = openai.OpenAI(api_key=self.api_key)
        self.model = model
        self.logger = logger
    
    def analyze_failure_patterns(self, low_confidence_results: List[Dict]) -> Dict:
        """Analyze failure patterns in low-confidence results"""
        if not low_confidence_results:
            return {"message": "No low-confidence results to analyze"}
        
        prompt = self._build_analysis_prompt(low_confidence_results)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1000
            )
            
            analysis = response.choices[0].message.content
            return self._parse_analysis_response(analysis)
            
        except Exception as e:
            self.logger.error(f"AI analysis failed: {e}")
            return {"error": str(e)}
    
    def suggest_rules(self, failure_patterns: Dict) -> List[Dict]:
        """Suggest new rules based on failure patterns"""
        prompt = self._build_rule_suggestion_prompt(failure_patterns)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=1500
            )
            
            suggestions = response.choices[0].message.content
            return self._parse_rule_suggestions(suggestions)
            
        except Exception as e:
            self.logger.error(f"Rule suggestion failed: {e}")
            return []
    
    def _build_analysis_prompt(self, results: List[Dict]) -> str:
        """Build prompt for failure pattern analysis"""
        examples = "\n".join([
            f"Original: {r.get('original_description', '')} -> Enhanced: {r.get('enhanced_description', '')} (Confidence: {r.get('confidence_level', 'Unknown')})"
            for r in results[:10]  # Limit to first 10 examples
        ])
        
        return f"""
        Analyze these low-confidence product description enhancement results and identify common failure patterns:
        
        {examples}
        
        Identify:
        1. Common patterns in original descriptions that weren't properly enhanced
        2. Missing rule categories (company names, specifications, dimensions, etc.)
        3. Context misinterpretations
        4. Specific examples that could benefit from new rules
        
        Provide analysis in JSON format with categories: patterns, missing_rules, context_issues, examples
        """
    
    def _build_rule_suggestion_prompt(self, patterns: Dict) -> str:
        """Build prompt for rule suggestions"""
        return f"""
        Based on this failure pattern analysis, suggest specific rules to improve the system:
        
        {json.dumps(patterns, indent=2)}
        
        For each suggestion, provide:
        1. Rule type (company, specification, dimension, product_type, etc.)
        2. Pattern/regex to match
        3. Replacement/expansion text
        4. Confidence level for the suggestion
        5. Reasoning
        
        Provide suggestions in JSON format as an array of objects.
        """
    
    def _parse_analysis_response(self, response: str) -> Dict:
        """Parse AI analysis response"""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {"raw_response": response}
        except Exception as e:
            self.logger.error(f"Failed to parse analysis response: {e}")
            return {"raw_response": response}
    
    def _parse_rule_suggestions(self, response: str) -> List[Dict]:
        """Parse AI rule suggestions"""
        try:
            # Extract JSON array from response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Try to extract multiple JSON objects
                json_objects = re.findall(r'\{[^{}]*\}', response)
                if json_objects:
                    return [json.loads(obj) for obj in json_objects]
                return []
        except Exception as e:
            self.logger.error(f"Failed to parse rule suggestions: {e}")
            return []
