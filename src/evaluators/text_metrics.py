"""
Text-based evaluation metrics.

Implements: accuracy, exact match (EM), F1, ROUGE-L, BLEU
Provides TextEvaluator class that inherits from BaseEvaluator.
"""

import re
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

from .base import BaseEvaluator, EvaluationResult


def normalize_text(text: str) -> str:
    """
    Normalize text for comparison.
    - Lowercase
    - Remove punctuation
    - Collapse whitespace
    """
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def exact_match(prediction: str, ground_truth: str, normalize: bool = True) -> bool:
    """
    Check if prediction exactly matches ground truth.
    
    Args:
        prediction: Model's predicted answer
        ground_truth: Ground truth answer
        normalize: Whether to normalize text before comparison
        
    Returns:
        True if exact match, False otherwise
    """
    if normalize:
        prediction = normalize_text(prediction)
        ground_truth = normalize_text(ground_truth)
    return prediction == ground_truth


def accuracy(predictions: List[str], ground_truths: List[str], normalize: bool = True) -> float:
    """
    Compute accuracy over a list of predictions.
    
    Args:
        predictions: List of predicted answers
        ground_truths: List of ground truth answers
        normalize: Whether to normalize text before comparison
        
    Returns:
        Accuracy score between 0 and 1
    """
    if len(predictions) != len(ground_truths):
        raise ValueError("predictions and ground_truths must have the same length")
    if len(predictions) == 0:
        return 0.0
    
    correct = sum(
        exact_match(pred, gt, normalize)
        for pred, gt in zip(predictions, ground_truths)
    )
    return correct / len(predictions)


def _get_tokens(text: str, normalize: bool = True) -> List[str]:
    """Tokenize text into words."""
    if normalize:
        text = normalize_text(text)
    return text.split()


def f1_score(prediction: str, ground_truth: str, normalize: bool = True) -> float:
    """
    Compute token-level F1 score between prediction and ground truth.
    
    Args:
        prediction: Model's predicted answer
        ground_truth: Ground truth answer
        normalize: Whether to normalize text before comparison
        
    Returns:
        F1 score between 0 and 1
    """
    pred_tokens = _get_tokens(prediction, normalize)
    gt_tokens = _get_tokens(ground_truth, normalize)
    
    if len(pred_tokens) == 0 and len(gt_tokens) == 0:
        return 1.0
    if len(pred_tokens) == 0 or len(gt_tokens) == 0:
        return 0.0
    
    pred_counter = Counter(pred_tokens)
    gt_counter = Counter(gt_tokens)
    
    common = sum((pred_counter & gt_counter).values())
    
    if common == 0:
        return 0.0
    
    precision = common / len(pred_tokens)
    recall = common / len(gt_tokens)
    
    return 2 * precision * recall / (precision + recall)


def _lcs_length(x: List[str], y: List[str]) -> int:
    """Compute length of longest common subsequence."""
    m, n = len(x), len(y)
    if m == 0 or n == 0:
        return 0
    
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if x[i - 1] == y[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    
    return dp[m][n]


def rouge_l(prediction: str, ground_truth: str, normalize: bool = True) -> Tuple[float, float, float]:
    """
    Compute ROUGE-L score (based on longest common subsequence).
    
    Args:
        prediction: Model's predicted answer
        ground_truth: Ground truth answer
        normalize: Whether to normalize text before comparison
        
    Returns:
        Tuple of (precision, recall, f1)
    """
    pred_tokens = _get_tokens(prediction, normalize)
    gt_tokens = _get_tokens(ground_truth, normalize)
    
    if len(pred_tokens) == 0 and len(gt_tokens) == 0:
        return (1.0, 1.0, 1.0)
    if len(pred_tokens) == 0 or len(gt_tokens) == 0:
        return (0.0, 0.0, 0.0)
    
    lcs_len = _lcs_length(pred_tokens, gt_tokens)
    
    precision = lcs_len / len(pred_tokens)
    recall = lcs_len / len(gt_tokens)
    
    if precision + recall == 0:
        f1 = 0.0
    else:
        f1 = 2 * precision * recall / (precision + recall)
    
    return (precision, recall, f1)


def rouge_l_f1(prediction: str, ground_truth: str, normalize: bool = True) -> float:
    """
    Compute ROUGE-L F1 score.
    
    Args:
        prediction: Model's predicted answer
        ground_truth: Ground truth answer
        normalize: Whether to normalize text before comparison
        
    Returns:
        ROUGE-L F1 score between 0 and 1
    """
    _, _, f1 = rouge_l(prediction, ground_truth, normalize)
    return f1


def _get_ngrams(tokens: List[str], n: int) -> Counter:
    """Extract n-grams from token list."""
    ngrams = [tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]
    return Counter(ngrams)


def bleu(
    prediction: str,
    ground_truth: str,
    max_n: int = 4,
    normalize: bool = True,
    weights: Optional[List[float]] = None
) -> float:
    """
    Compute BLEU score (simplified single-reference version).
    
    Args:
        prediction: Model's predicted answer
        ground_truth: Ground truth answer
        max_n: Maximum n-gram order (default 4)
        normalize: Whether to normalize text before comparison
        weights: Weights for each n-gram order (default: uniform)
        
    Returns:
        BLEU score between 0 and 1
    """
    pred_tokens = _get_tokens(prediction, normalize)
    gt_tokens = _get_tokens(ground_truth, normalize)
    
    if len(pred_tokens) == 0:
        return 0.0
    if len(gt_tokens) == 0:
        return 0.0
    
    effective_max_n = min(max_n, len(pred_tokens), len(gt_tokens))
    if effective_max_n == 0:
        return 0.0
    
    if weights is None:
        weights = [1.0 / effective_max_n] * effective_max_n
    else:
        weights = weights[:effective_max_n]
        weight_sum = sum(weights)
        if weight_sum > 0:
            weights = [w / weight_sum for w in weights]
    
    precisions = []
    for n in range(1, effective_max_n + 1):
        pred_ngrams = _get_ngrams(pred_tokens, n)
        gt_ngrams = _get_ngrams(gt_tokens, n)
        
        if len(pred_ngrams) == 0:
            precisions.append(0.0)
            continue
        
        clipped_count = sum((pred_ngrams & gt_ngrams).values())
        total_count = sum(pred_ngrams.values())
        
        precisions.append(clipped_count / total_count if total_count > 0 else 0.0)
    
    if any(p == 0 for p in precisions):
        return 0.0
    
    import math
    log_precision = sum(w * math.log(p) for w, p in zip(weights, precisions))
    
    bp = 1.0
    if len(pred_tokens) < len(gt_tokens):
        bp = math.exp(1 - len(gt_tokens) / len(pred_tokens))
    
    return bp * math.exp(log_precision)


def compute_all_metrics(
    prediction: str,
    ground_truth: str,
    normalize: bool = True
) -> dict:
    """
    Compute all text metrics for a single prediction.
    
    Args:
        prediction: Model's predicted answer
        ground_truth: Ground truth answer
        normalize: Whether to normalize text before comparison
        
    Returns:
        Dictionary with all metric scores
    """
    return {
        "exact_match": exact_match(prediction, ground_truth, normalize),
        "f1": f1_score(prediction, ground_truth, normalize),
        "rouge_l_f1": rouge_l_f1(prediction, ground_truth, normalize),
        "bleu": bleu(prediction, ground_truth, normalize=normalize),
    }


class TextEvaluator(BaseEvaluator):
    """
    Text-based evaluator for QA and generation tasks.
    
    Computes: Accuracy, Exact Match (EM), F1, ROUGE-L
    """
    
    def __init__(
        self,
        name: Optional[str] = None,
        normalize: bool = True,
        metrics: Optional[List[str]] = None
    ):
        """
        Initialize TextEvaluator.
        
        Args:
            name: Optional evaluator name
            normalize: Whether to normalize text before comparison
            metrics: List of metrics to compute. Default: all metrics.
                     Options: 'accuracy', 'em', 'f1', 'rouge_l'
        """
        super().__init__(name=name)
        self.normalize = normalize
        self.metrics = metrics or ["accuracy", "em", "f1", "rouge_l"]
    
    def compute(
        self,
        predictions: List[str],
        references: List[str],
        **kwargs
    ) -> EvaluationResult:
        """
        Compute text evaluation metrics.
        
        Args:
            predictions: List of model predictions
            references: List of ground truth references
            **kwargs: Additional arguments (e.g., normalize override)
            
        Returns:
            EvaluationResult with metrics and per-sample details
        """
        self.validate_inputs(predictions, references)
        
        normalize = kwargs.get("normalize", self.normalize)
        
        details = []
        em_scores = []
        f1_scores = []
        rouge_l_scores = []
        
        for pred, ref in zip(predictions, references):
            em = exact_match(pred, ref, normalize)
            f1 = f1_score(pred, ref, normalize)
            rl = rouge_l_f1(pred, ref, normalize)
            
            em_scores.append(em)
            f1_scores.append(f1)
            rouge_l_scores.append(rl)
            
            details.append({
                "prediction": pred,
                "reference": ref,
                "exact_match": em,
                "f1": f1,
                "rouge_l": rl,
            })
        
        n = len(predictions)
        metrics_dict: Dict[str, float] = {}
        
        if "accuracy" in self.metrics or "em" in self.metrics:
            metrics_dict["accuracy"] = sum(em_scores) / n
            metrics_dict["em"] = metrics_dict["accuracy"]
        
        if "f1" in self.metrics:
            metrics_dict["f1"] = sum(f1_scores) / n
        
        if "rouge_l" in self.metrics:
            metrics_dict["rouge_l"] = sum(rouge_l_scores) / n
        
        return EvaluationResult(
            metrics=metrics_dict,
            details=details,
            metadata={
                "total_samples": n,
                "correct_samples": sum(em_scores),
                "normalize": normalize,
            }
        )
