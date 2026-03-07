"""
Choice-based evaluation metrics for multiple choice questions.

Implements: choice accuracy, answer extraction, option bias analysis
Provides ChoiceEvaluator class that inherits from BaseEvaluator.
"""

import re
from collections import Counter
from typing import Any, Dict, List, Optional, Set

from .base import BaseEvaluator, EvaluationResult


VALID_OPTIONS = {"A", "B", "C", "D", "E", "F"}


NEGATION_WORDS = {
    "不是", "不选", "不对", "不正确", "排除", "错误", "不应该", "不会是",
    "not", "isn't", "aren't", "wrong", "incorrect", "exclude", "eliminate",
}

UNCERTAINTY_WORDS = {
    "可能", "大概", "也许", "或许", "不确定", "不太确定", "不太清楚", "猜测",
    "maybe", "perhaps", "probably", "possibly", "uncertain", "unsure", "guess",
    "might be", "could be", "not sure", "hard to say",
}

FINAL_ANSWER_MARKERS = {
    "最终答案", "最终选择", "最后答案", "综上所述", "因此答案", "所以答案",
    "final answer", "therefore", "thus", "in conclusion", "so the answer",
    "hence", "consequently",
}


def _has_uncertainty(text: str) -> bool:
    """Check if text contains uncertainty expressions without final answer markers."""
    text_lower = text.lower()
    
    has_uncertainty = any(word in text_lower for word in UNCERTAINTY_WORDS)
    has_final_marker = any(marker in text_lower for marker in FINAL_ANSWER_MARKERS)
    
    return has_uncertainty and not has_final_marker


def _find_negated_options(text: str, valid_options: Set[str]) -> Set[str]:
    """Find options that are negated in the text."""
    negated = set()
    options_pattern = "|".join(valid_options)
    
    negation_patterns = [
        rf"(?:不是|不选|不对|排除|错误的?是?|不应该选?|不会是)\s*[(\[]*({options_pattern})[)\]]*",
        rf"({options_pattern})\s*(?:不对|不正确|是错的|错误|应该排除)",
        rf"(?:not|isn't|aren't|wrong|incorrect|exclude|eliminate)\s+[(\[]*({options_pattern})[)\]]*",
        rf"({options_pattern})\s+(?:is wrong|is incorrect|should be excluded)",
    ]
    
    for pattern in negation_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            negated.add(match.group(1).upper())
    
    return negated


def extract_choice(text: str, valid_options: Optional[Set[str]] = None) -> Optional[str]:
    """
    Extract the chosen option from model output with enhanced parsing.
    
    Features:
    - Enhanced Chinese pattern matching (答案应该是A, 选项是C, etc.)
    - Negation detection (不是A，我觉得是B -> returns B)
    - Uncertainty filtering (可能是C，但不确定 -> returns None)
    - CoT ending format support (Therefore, the answer is A. / >>> A)
    
    Supports various formats:
    - "A" or "a"
    - "The answer is A" / "Therefore, the answer is option A"
    - "Answer: A" / ">>> A"
    - "(A)" or "[A]"
    - "选择A" / "答案是A" / "答案应该是A" / "选项是C"
    - "A选项最符合" / "A是正确答案"
    
    Args:
        text: Model output text
        valid_options: Set of valid option letters (default: A-F)
        
    Returns:
        Extracted option letter (uppercase) or None if not found/uncertain
    """
    if valid_options is None:
        valid_options = VALID_OPTIONS
    
    text = text.strip()
    
    if not text:
        return None
    
    if _has_uncertainty(text):
        return None
    
    negated_options = _find_negated_options(text, valid_options)
    
    options_pattern = "|".join(valid_options)
    
    high_priority_patterns = [
        rf"(?:最终答案|最终选择|最后答案|综上所述|因此答案|所以答案)[是为:：\s]*[(\[]*({options_pattern})[)\]]*",
        rf"(?:final answer|therefore|thus|hence|in conclusion)[,\s:]*(?:the answer is\s*)?(?:option\s*)?[(\[]*({options_pattern})[)\]]*",
        rf">>>\s*({options_pattern})",
    ]
    
    for pattern in high_priority_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            option = match.group(1).upper()
            if option not in negated_options:
                return option
    
    chinese_patterns = [
        rf"(?:答案|选项|选|最终结果|正确答案)(?:应该|应|就)?(?:是|为|：|:)\s*[(\[]*({options_pattern})[)\]]*",
        rf"(?:我选|我认为是|应该选|选择了?|我觉得是|认为是|应该是)\s*[(\[]*({options_pattern})[)\]]*",
        rf"({options_pattern})\s*(?:选项|项)?(?:最符合|是正确答案|是对的|正确|是答案)",
        rf"(?:是|为)\s*({options_pattern})(?:\s|$|[.。,，])",
    ]
    
    english_statement_patterns = [
        rf"(?:option\s+)?({options_pattern})\s+(?:is|is the)\s+(?:correct|right|best|proper|appropriate)(?:\s+(?:answer|choice|option))?",
        rf"(?:I think|I believe|I'd say)\s+(?:option\s+)?({options_pattern})\s+is\s+(?:correct|right|the answer)",
        rf"({options_pattern})\s+is\s+(?:the\s+)?(?:best|correct|right)\s+(?:answer|choice|option)",
        rf"(?:the\s+)?(?:correct|right|best)\s+(?:answer|choice|option)\s+is\s+({options_pattern})",
    ]
    
    english_patterns = [
        rf"(?:answer|choice|option)[\s:：]*(?:is|should be|would be)?\s*[(\[]*({options_pattern})[)\]]*",
        rf"(?:I (?:choose|pick|select|think it's|believe it's))\s*[(\[]*({options_pattern})[)\]]*",
        rf"\bis\s+(?:option\s+)?({options_pattern})(?:\s|$|[.。,，])",
        rf"(?:select|choose|pick)\s+(?:option\s+)?({options_pattern})",
    ]
    
    bracket_patterns = [
        rf"[(\[]+({options_pattern})[)\]]+",
    ]
    
    boundary_patterns = [
        rf"^({options_pattern})[\s.。,，:：)\]]",
        rf"[\s]({options_pattern})[\s.。,，]?$",
        rf"^({options_pattern})$",
    ]
    
    all_patterns = chinese_patterns + english_statement_patterns + english_patterns + bracket_patterns + boundary_patterns
    
    for pattern in all_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            option = match.group(1).upper()
            if option not in negated_options:
                return option
    
    return None


def choice_accuracy(
    predictions: List[str],
    references: List[str],
    valid_options: Optional[Set[str]] = None
) -> float:
    """
    Compute accuracy for multiple choice questions.
    
    Args:
        predictions: List of model outputs (will be parsed to extract choice)
        references: List of ground truth answers (single letters)
        valid_options: Set of valid option letters
        
    Returns:
        Accuracy score between 0 and 1
    """
    if len(predictions) != len(references):
        raise ValueError("predictions and references must have the same length")
    if len(predictions) == 0:
        return 0.0
    
    correct = 0
    for pred, ref in zip(predictions, references):
        extracted = extract_choice(pred, valid_options)
        ref_normalized = ref.strip().upper()
        if extracted == ref_normalized:
            correct += 1
    
    return correct / len(predictions)


def compute_option_bias(
    predictions: List[str],
    references: List[str],
    valid_options: Optional[Set[str]] = None
) -> Dict[str, Any]:
    """
    Analyze option selection bias in model predictions.
    
    Computes:
    - Distribution of predicted options
    - Distribution of ground truth options
    - Per-option accuracy
    - Bias score (deviation from uniform distribution)
    
    Args:
        predictions: List of model outputs
        references: List of ground truth answers
        valid_options: Set of valid option letters
        
    Returns:
        Dictionary with bias analysis results
    """
    if valid_options is None:
        valid_options = VALID_OPTIONS
    
    pred_counts: Counter = Counter()
    ref_counts: Counter = Counter()
    option_correct: Dict[str, int] = {opt: 0 for opt in valid_options}
    option_total: Dict[str, int] = {opt: 0 for opt in valid_options}
    
    extracted_preds = []
    for pred, ref in zip(predictions, references):
        extracted = extract_choice(pred, valid_options)
        ref_normalized = ref.strip().upper()
        
        extracted_preds.append(extracted)
        
        if extracted:
            pred_counts[extracted] += 1
        else:
            pred_counts["INVALID"] += 1
        
        if ref_normalized in valid_options:
            ref_counts[ref_normalized] += 1
            option_total[ref_normalized] += 1
            
            if extracted == ref_normalized:
                option_correct[ref_normalized] += 1
    
    n = len(predictions)
    
    pred_distribution = {
        opt: pred_counts.get(opt, 0) / n if n > 0 else 0.0
        for opt in valid_options
    }
    pred_distribution["INVALID"] = pred_counts.get("INVALID", 0) / n if n > 0 else 0.0
    
    ref_distribution = {
        opt: ref_counts.get(opt, 0) / n if n > 0 else 0.0
        for opt in valid_options
    }
    
    per_option_accuracy = {}
    for opt in valid_options:
        if option_total[opt] > 0:
            per_option_accuracy[opt] = option_correct[opt] / option_total[opt]
        else:
            per_option_accuracy[opt] = None
    
    active_options = [opt for opt in valid_options if ref_counts.get(opt, 0) > 0]
    if len(active_options) > 0:
        uniform_prob = 1.0 / len(active_options)
        bias_score = sum(
            abs(pred_distribution.get(opt, 0) - uniform_prob)
            for opt in active_options
        ) / len(active_options)
    else:
        bias_score = 0.0
    
    return {
        "prediction_distribution": pred_distribution,
        "reference_distribution": ref_distribution,
        "per_option_accuracy": per_option_accuracy,
        "bias_score": bias_score,
        "invalid_count": pred_counts.get("INVALID", 0),
        "invalid_rate": pred_counts.get("INVALID", 0) / n if n > 0 else 0.0,
    }


class ChoiceEvaluator(BaseEvaluator):
    """
    Evaluator for multiple choice questions.
    
    Computes: Choice Accuracy, Option Bias Analysis
    Handles answer extraction from various output formats.
    """
    
    def __init__(
        self,
        name: Optional[str] = None,
        valid_options: Optional[Set[str]] = None,
        analyze_bias: bool = True
    ):
        """
        Initialize ChoiceEvaluator.
        
        Args:
            name: Optional evaluator name
            valid_options: Set of valid option letters (default: A-F)
            analyze_bias: Whether to compute option bias analysis
        """
        super().__init__(name=name)
        self.valid_options = valid_options or VALID_OPTIONS
        self.analyze_bias = analyze_bias
    
    def compute(
        self,
        predictions: List[str],
        references: List[str],
        **kwargs
    ) -> EvaluationResult:
        """
        Compute choice evaluation metrics.
        
        Args:
            predictions: List of model outputs (raw text)
            references: List of ground truth answers (option letters)
            **kwargs: Additional arguments
            
        Returns:
            EvaluationResult with metrics, details, and bias analysis
        """
        self.validate_inputs(predictions, references)
        
        valid_options = kwargs.get("valid_options", self.valid_options)
        
        details = []
        correct_count = 0
        
        for pred, ref in zip(predictions, references):
            extracted = extract_choice(pred, valid_options)
            ref_normalized = ref.strip().upper()
            is_correct = extracted == ref_normalized
            
            if is_correct:
                correct_count += 1
            
            details.append({
                "raw_prediction": pred,
                "extracted_answer": extracted,
                "reference": ref_normalized,
                "correct": is_correct,
            })
        
        n = len(predictions)
        accuracy = correct_count / n if n > 0 else 0.0
        
        metrics_dict = {
            "accuracy": accuracy,
            "choice_accuracy": accuracy,
        }
        
        metadata = {
            "total_samples": n,
            "correct_samples": correct_count,
            "valid_options": list(valid_options),
        }
        
        if self.analyze_bias:
            bias_analysis = compute_option_bias(predictions, references, valid_options)
            metrics_dict["bias_score"] = bias_analysis["bias_score"]
            metrics_dict["invalid_rate"] = bias_analysis["invalid_rate"]
            metadata["bias_analysis"] = bias_analysis
        
        return EvaluationResult(
            metrics=metrics_dict,
            details=details,
            metadata=metadata
        )
