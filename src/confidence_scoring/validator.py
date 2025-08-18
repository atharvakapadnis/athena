# src/confidence_scoring/validator.py
from typing import Dict, List, Tuple
import numpy as np

try:
    from sklearn.metrics import classification_report, confusion_matrix
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: sklearn not available. Some validation features will be limited.")

class QualityValidator:
    """Validates confidence scores against actual quality"""
    
    def __init__(self):
        self.validation_history = []
    
    def validate_confidence_calibration(self, results: List[Dict], 
                                      actual_quality: List[bool]) -> Dict:
        """Validate if confidence scores align with actual quality"""
        if len(results) != len(actual_quality):
            raise ValueError("Results and actual quality must have same length")
        
        # Create quality predictions based on confidence
        predicted_quality = [r.get('confidence_score', 0.0) > 0.7 for r in results]
        
        validation_result = {}
        
        # Calculate metrics with sklearn if available
        if SKLEARN_AVAILABLE:
            report = classification_report(actual_quality, predicted_quality, 
                                         output_dict=True)
            validation_result['classification_report'] = report
        else:
            # Simple accuracy calculation
            correct = sum(1 for i, pred in enumerate(predicted_quality) 
                         if pred == actual_quality[i])
            validation_result['accuracy'] = correct / len(actual_quality)
        
        # Calculate calibration error
        calibration_error = self._calculate_calibration_error(results, actual_quality)
        
        validation_result.update({
            'calibration_error': calibration_error,
            'confidence_quality_correlation': self._calculate_correlation(results, actual_quality),
            'is_well_calibrated': calibration_error < 0.1
        })
        
        self.validation_history.append(validation_result)
        return validation_result
    
    def _calculate_calibration_error(self, results: List[Dict], 
                                   actual_quality: List[bool]) -> float:
        """Calculate confidence calibration error"""
        # Group by confidence bins
        bins = np.linspace(0, 1, 11)
        bin_centers = (bins[:-1] + bins[1:]) / 2
        
        calibration_errors = []
        
        for i in range(len(bins) - 1):
            bin_mask = (np.array([r.get('confidence_score', 0.0) for r in results]) >= bins[i]) & \
                      (np.array([r.get('confidence_score', 0.0) for r in results]) < bins[i + 1])
            
            if bin_mask.sum() > 0:
                predicted_confidence = bin_centers[i]
                actual_accuracy = np.array(actual_quality)[bin_mask].mean()
                calibration_errors.append(abs(predicted_confidence - actual_accuracy))
        
        return np.mean(calibration_errors) if calibration_errors else 0.0
    
    def _calculate_correlation(self, results: List[Dict], 
                             actual_quality: List[bool]) -> float:
        """Calculate correlation between confidence and actual quality"""
        confidence_scores = [r.get('confidence_score', 0.0) for r in results]
        try:
            return np.corrcoef(confidence_scores, actual_quality)[0, 1]
        except:
            # Fallback if correlation calculation fails
            return 0.0
