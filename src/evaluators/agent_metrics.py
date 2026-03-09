"""
Agent evaluation metrics.

Implements:
- Action Success Rate: Fraction of tool calls that executed successfully
- Parameter Accuracy: Fraction of tool call parameters that match expected values

Input requirements:
- tool_calls: List of tool call trace logs with expected and actual results
"""

from typing import Any, Dict, List, Optional, Set

from .base import BaseEvaluator, EvaluationResult


class AgentEvaluator(BaseEvaluator):
    """
    Evaluator for agent/tool-calling tasks.
    
    Computes action success rate and parameter accuracy based on tool call traces.
    """
    
    def __init__(self, name: Optional[str] = None):
        """
        Initialize agent evaluator.
        
        Args:
            name: Optional evaluator name
        """
        super().__init__(name=name)
    
    def compute(
        self,
        predictions: List[str],
        references: List[str],
        tool_calls: Optional[List[List[Dict[str, Any]]]] = None,
        **kwargs
    ) -> EvaluationResult:
        """
        Compute agent metrics.
        
        Args:
            predictions: List of model predictions (for interface compatibility)
            references: List of ground truth answers (for interface compatibility)
            tool_calls: List of tool call trace lists per sample
                Each tool call dict should contain:
                - tool_name: Name of the tool called
                - parameters: Dict of parameters passed
                - expected_parameters: Dict of expected parameters (optional)
                - success: Whether the call succeeded
                - expected_tool: Expected tool name (optional)
            
        Returns:
            EvaluationResult with action_success_rate and parameter_accuracy metrics
        """
        if tool_calls is None:
            raise ValueError("tool_calls is required (list of tool call trace lists)")
        
        n = len(tool_calls)
        if n == 0:
            return EvaluationResult(
                metrics={
                    "action_success_rate": 0.0,
                    "parameter_accuracy": 0.0,
                    "tool_selection_accuracy": 0.0,
                },
                metadata={"total_samples": 0, "total_calls": 0}
            )
        
        total_calls = 0
        successful_calls = 0
        correct_tool_selections = 0
        total_params = 0
        correct_params = 0
        details = []
        
        for sample_idx, sample_calls in enumerate(tool_calls):
            sample_success = 0
            sample_tool_correct = 0
            sample_param_total = 0
            sample_param_correct = 0
            
            for call in sample_calls:
                total_calls += 1
                
                # Check action success
                if call.get("success", False):
                    successful_calls += 1
                    sample_success += 1
                
                # Check tool selection accuracy
                expected_tool = call.get("expected_tool")
                actual_tool = call.get("tool_name")
                if expected_tool and actual_tool:
                    if expected_tool == actual_tool:
                        correct_tool_selections += 1
                        sample_tool_correct += 1
                
                # Check parameter accuracy
                expected_params = call.get("expected_parameters", {})
                actual_params = call.get("parameters", {})
                
                if expected_params:
                    for key, expected_value in expected_params.items():
                        total_params += 1
                        sample_param_total += 1
                        actual_value = actual_params.get(key)
                        
                        # Compare values (handle type differences)
                        if self._values_match(expected_value, actual_value):
                            correct_params += 1
                            sample_param_correct += 1
            
            num_calls = len(sample_calls)
            details.append({
                "sample_index": sample_idx,
                "num_calls": num_calls,
                "successful_calls": sample_success,
                "success_rate": round(sample_success / num_calls, 4) if num_calls > 0 else 0.0,
                "param_accuracy": round(sample_param_correct / sample_param_total, 4) if sample_param_total > 0 else 1.0,
            })
        
        # Compute aggregate metrics
        action_success_rate = successful_calls / total_calls if total_calls > 0 else 0.0
        tool_selection_accuracy = correct_tool_selections / total_calls if total_calls > 0 else 0.0
        parameter_accuracy = correct_params / total_params if total_params > 0 else 1.0
        
        return EvaluationResult(
            metrics={
                "action_success_rate": round(action_success_rate, 4),
                "tool_selection_accuracy": round(tool_selection_accuracy, 4),
                "parameter_accuracy": round(parameter_accuracy, 4),
            },
            details=details,
            metadata={
                "total_samples": n,
                "total_calls": total_calls,
                "successful_calls": successful_calls,
                "correct_tool_selections": correct_tool_selections,
                "total_params": total_params,
                "correct_params": correct_params,
            }
        )
    
    def _values_match(self, expected: Any, actual: Any) -> bool:
        """
        Check if two values match, handling type differences.
        
        Args:
            expected: Expected value
            actual: Actual value
            
        Returns:
            True if values match
        """
        if expected == actual:
            return True
        
        # Handle string/number comparisons
        try:
            if str(expected).lower() == str(actual).lower():
                return True
        except (ValueError, TypeError):
            pass
        
        # Handle list comparisons (order-insensitive)
        if isinstance(expected, list) and isinstance(actual, list):
            return set(map(str, expected)) == set(map(str, actual))
        
        return False


def action_success_rate(tool_calls: List[List[Dict[str, Any]]]) -> float:
    """
    Compute action success rate: fraction of tool calls that succeeded.
    
    Args:
        tool_calls: List of tool call trace lists per sample
            Each call dict should have 'success' field
            
    Returns:
        Success rate as a float between 0 and 1
    """
    if not tool_calls:
        return 0.0
    
    total = 0
    successful = 0
    
    for sample_calls in tool_calls:
        for call in sample_calls:
            total += 1
            if call.get("success", False):
                successful += 1
    
    return successful / total if total > 0 else 0.0


def parameter_accuracy(tool_calls: List[List[Dict[str, Any]]]) -> float:
    """
    Compute parameter accuracy: fraction of parameters that match expected values.
    
    Args:
        tool_calls: List of tool call trace lists per sample
            Each call dict should have 'parameters' and 'expected_parameters' fields
            
    Returns:
        Accuracy as a float between 0 and 1
    """
    if not tool_calls:
        return 0.0
    
    total_params = 0
    correct_params = 0
    
    for sample_calls in tool_calls:
        for call in sample_calls:
            expected = call.get("expected_parameters", {})
            actual = call.get("parameters", {})
            
            for key, expected_value in expected.items():
                total_params += 1
                actual_value = actual.get(key)
                
                if expected_value == actual_value:
                    correct_params += 1
                elif str(expected_value).lower() == str(actual_value).lower():
                    correct_params += 1
    
    return correct_params / total_params if total_params > 0 else 1.0


def tool_selection_accuracy(tool_calls: List[List[Dict[str, Any]]]) -> float:
    """
    Compute tool selection accuracy: fraction of calls where correct tool was selected.
    
    Args:
        tool_calls: List of tool call trace lists per sample
            Each call dict should have 'tool_name' and 'expected_tool' fields
            
    Returns:
        Accuracy as a float between 0 and 1
    """
    if not tool_calls:
        return 0.0
    
    total = 0
    correct = 0
    
    for sample_calls in tool_calls:
        for call in sample_calls:
            expected_tool = call.get("expected_tool")
            actual_tool = call.get("tool_name")
            
            if expected_tool:
                total += 1
                if expected_tool == actual_tool:
                    correct += 1
    
    return correct / total if total > 0 else 0.0
