# src/confidence_scoring/calibrator.py
from typing import Dict, List, Callable
import numpy as np

try:
    from sklearn.isotonic import IsotonicRegression
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: sklearn not available. Calibration will use simple linear scaling.")

class ConfidenceCalibrator:
    """Calibrates confidence scores based on historical performance"""
    
    def __init__(self):
        self.calibration_model = None
        self.is_calibrated = False
        self.linear_params = None
    
    def calibrate_scores(self, confidence_scores: List[float], 
                        actual_quality: List[bool]) -> List[float]:
        """Calibrate confidence scores using isotonic regression or linear scaling"""
        if len(confidence_scores) != len(actual_quality):
            raise ValueError("Scores and quality must have same length")
        
        if SKLEARN_AVAILABLE:
            # Use isotonic regression
            self.calibration_model = IsotonicRegression(out_of_bounds='clip')
            self.calibration_model.fit(confidence_scores, actual_quality)
            calibrated_scores = self.calibration_model.predict(confidence_scores)
        else:
            # Use simple linear calibration
            self._fit_linear_calibration(confidence_scores, actual_quality)
            calibrated_scores = self._apply_linear_calibration(confidence_scores)
        
        self.is_calibrated = True
        return calibrated_scores.tolist() if hasattr(calibrated_scores, 'tolist') else calibrated_scores
    
    def apply_calibration(self, confidence_scores: List[float]) -> List[float]:
        """Apply trained calibration to new scores"""
        if not self.is_calibrated:
            return confidence_scores
        
        if SKLEARN_AVAILABLE and self.calibration_model is not None:
            return self.calibration_model.predict(confidence_scores).tolist()
        elif self.linear_params is not None:
            return self._apply_linear_calibration(confidence_scores)
        else:
            return confidence_scores
    
    def _fit_linear_calibration(self, confidence_scores: List[float], 
                               actual_quality: List[bool]):
        """Fit simple linear calibration parameters"""
        # Convert to numpy arrays
        scores = np.array(confidence_scores)
        quality = np.array(actual_quality, dtype=float)
        
        # Simple linear regression: y = ax + b
        if len(scores) > 1:
            a = np.corrcoef(scores, quality)[0, 1] * np.std(quality) / np.std(scores)
            b = np.mean(quality) - a * np.mean(scores)
            self.linear_params = (a, b)
        else:
            self.linear_params = (1.0, 0.0)
    
    def _apply_linear_calibration(self, confidence_scores: List[float]) -> List[float]:
        """Apply linear calibration"""
        if self.linear_params is None:
            return confidence_scores
        
        a, b = self.linear_params
        calibrated = [max(0.0, min(1.0, a * score + b)) for score in confidence_scores]
        return calibrated
    
    def get_calibration_quality(self) -> Dict:
        """Get calibration model quality metrics"""
        if not self.is_calibrated:
            return {"is_calibrated": False}
        
        if SKLEARN_AVAILABLE and self.calibration_model is not None:
            return {
                "is_calibrated": True,
                "model_type": "IsotonicRegression",
                "out_of_bounds": "clip"
            }
        elif self.linear_params is not None:
            return {
                "is_calibrated": True,
                "model_type": "LinearCalibration",
                "parameters": self.linear_params
            }
        else:
            return {"is_calibrated": False}
