"""
Base evaluator abstract class.

All evaluators inherit from BaseEvaluator and implement the compute() method.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class EvaluationResult:
    """Container for evaluation results."""
    
    def __init__(
        self,
        metrics: Dict[str, float],
        details: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize evaluation result.
        
        Args:
            metrics: Dictionary of metric names to values
            details: Optional per-sample details
            metadata: Optional metadata about the evaluation
        """
        self.metrics = metrics
        self.details = details or []
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "metrics": self.metrics,
            "details": self.details,
            "metadata": self.metadata,
        }
    
    def __repr__(self) -> str:
        return f"EvaluationResult(metrics={self.metrics})"


class BaseEvaluator(ABC):
    """
    Abstract base class for all evaluators.
    
    Subclasses must implement the compute() method to calculate
    evaluation metrics for predictions against references.
    """
    
    def __init__(self, name: Optional[str] = None):
        """
        Initialize evaluator.
        
        Args:
            name: Optional name for this evaluator instance
        """
        self.name = name or self.__class__.__name__
    
    @abstractmethod
    def compute(
        self,
        predictions: List[str],
        references: List[str],
        **kwargs
    ) -> EvaluationResult:
        """
        Compute evaluation metrics.
        
        Args:
            predictions: List of model predictions
            references: List of ground truth references
            **kwargs: Additional arguments specific to the evaluator
            
        Returns:
            EvaluationResult containing metrics and optional details
        """
        pass
    
    def validate_inputs(self, predictions: List[str], references: List[str]) -> None:
        """
        Validate that predictions and references are compatible.
        
        Args:
            predictions: List of model predictions
            references: List of ground truth references
            
        Raises:
            ValueError: If inputs are invalid
        """
        if len(predictions) != len(references):
            raise ValueError(
                f"Length mismatch: {len(predictions)} predictions vs {len(references)} references"
            )
        if len(predictions) == 0:
            raise ValueError("Empty input: predictions and references cannot be empty")
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
