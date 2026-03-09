"""
Unit tests for evaluators module.

Run with: python -m pytest tests/test_evaluators.py -v
Or directly: python tests/test_evaluators.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from evaluators import BaseEvaluator, EvaluationResult, TextEvaluator, ChoiceEvaluator
from evaluators.choice_metrics import extract_choice, compute_option_bias


def test_evaluation_result():
    """Test EvaluationResult container."""
    result = EvaluationResult(
        metrics={"accuracy": 0.8, "f1": 0.75},
        details=[{"sample": 1}],
        metadata={"total": 10}
    )
    
    assert result.metrics["accuracy"] == 0.8
    assert result.metrics["f1"] == 0.75
    assert len(result.details) == 1
    assert result.metadata["total"] == 10
    
    d = result.to_dict()
    assert "metrics" in d
    assert "details" in d
    assert "metadata" in d
    
    print("✓ test_evaluation_result passed")


def test_text_evaluator():
    """Test TextEvaluator."""
    evaluator = TextEvaluator()
    
    predictions = ["hello world", "foo bar", "test"]
    references = ["hello world", "foo baz", "test"]
    
    result = evaluator.compute(predictions, references)
    
    assert "accuracy" in result.metrics
    assert "f1" in result.metrics
    assert "rouge_l" in result.metrics
    
    assert result.metrics["accuracy"] == 2/3
    
    assert len(result.details) == 3
    assert result.metadata["total_samples"] == 3
    assert result.metadata["correct_samples"] == 2
    
    print("✓ test_text_evaluator passed")


def test_text_evaluator_perfect_match():
    """Test TextEvaluator with perfect matches."""
    evaluator = TextEvaluator()
    
    predictions = ["answer one", "answer two"]
    references = ["answer one", "answer two"]
    
    result = evaluator.compute(predictions, references)
    
    assert result.metrics["accuracy"] == 1.0
    assert result.metrics["f1"] == 1.0
    assert result.metrics["rouge_l"] == 1.0
    
    print("✓ test_text_evaluator_perfect_match passed")


def test_extract_choice():
    """Test choice extraction from various formats."""
    # Basic formats
    assert extract_choice("A") == "A"
    assert extract_choice("a") == "A"
    assert extract_choice("(D)") == "D"
    assert extract_choice("[A]") == "A"
    
    # English patterns
    assert extract_choice("The answer is B") == "B"
    assert extract_choice("Answer: C") == "C"
    assert extract_choice("I think the answer is A because...") == "A"
    
    # Empty/invalid
    assert extract_choice("") is None
    assert extract_choice("no answer here xyz") is None
    
    print("✓ test_extract_choice passed")


def test_extract_choice_english_statements():
    """Test English declarative statement patterns."""
    # Option at sentence start with "is correct/right/best"
    assert extract_choice("I think D is correct") == "D"
    assert extract_choice("Option A is the right choice") == "A"
    assert extract_choice("C is the best answer among them") == "C"
    
    # More variations
    assert extract_choice("B is correct") == "B"
    assert extract_choice("A is the correct answer") == "A"
    assert extract_choice("I believe B is right") == "B"
    assert extract_choice("D is the right option") == "D"
    assert extract_choice("The correct answer is C") == "C"
    assert extract_choice("The best choice is A") == "A"
    
    print("✓ test_extract_choice_english_statements passed")


def test_extract_choice_chinese():
    """Test enhanced Chinese pattern matching."""
    # Basic Chinese patterns
    assert extract_choice("选择B") == "B"
    assert extract_choice("答案是C") == "C"
    assert extract_choice("答案：D") == "D"
    
    # Enhanced Chinese patterns
    assert extract_choice("答案应该是A") == "A"
    assert extract_choice("选项是C") == "C"
    assert extract_choice("我选B") == "B"
    assert extract_choice("应该选D") == "D"
    assert extract_choice("正确答案是A") == "A"
    
    # Suffix patterns
    assert extract_choice("A选项最符合") == "A"
    assert extract_choice("B是正确答案") == "B"
    assert extract_choice("C是对的") == "C"
    
    print("✓ test_extract_choice_chinese passed")


def test_extract_choice_negation():
    """Test negation detection - skip negated options."""
    # Should skip negated option and find the affirmed one
    assert extract_choice("不是A，我觉得是B") == "B"
    assert extract_choice("排除A，答案是C") == "C"
    assert extract_choice("A不对，应该选B") == "B"
    assert extract_choice("A is wrong, the answer is B") == "B"
    assert extract_choice("Not A, I think it's C") == "C"
    
    # Only negated option - should return None
    assert extract_choice("不是A") is None
    assert extract_choice("A is wrong") is None
    
    print("✓ test_extract_choice_negation passed")


def test_extract_choice_uncertainty():
    """Test uncertainty filtering - return None for uncertain responses."""
    # Uncertain without final answer marker
    assert extract_choice("可能是C，但不确定") is None
    assert extract_choice("大概是A吧") is None
    assert extract_choice("也许是B") is None
    assert extract_choice("Maybe it's A, I'm not sure") is None
    assert extract_choice("Probably B, but uncertain") is None
    
    # Uncertain WITH final answer marker - should extract
    assert extract_choice("可能是A，但最终答案是B") == "B"
    assert extract_choice("I was unsure, but therefore the answer is C") == "C"
    
    print("✓ test_extract_choice_uncertainty passed")


def test_extract_choice_cot():
    """Test CoT (Chain of Thought) ending formats."""
    # CoT ending patterns
    assert extract_choice("Therefore, the answer is A") == "A"
    assert extract_choice("Thus, the answer is option B") == "B"
    assert extract_choice("In conclusion, C is correct") == "C"
    assert extract_choice(">>> A") == "A"
    assert extract_choice(">>> B") == "B"
    
    # Chinese CoT endings
    assert extract_choice("综上所述，答案是A") == "A"
    assert extract_choice("因此答案是B") == "B"
    assert extract_choice("所以答案是C") == "C"
    assert extract_choice("最终答案是D") == "D"
    
    print("✓ test_extract_choice_cot passed")


def test_choice_evaluator():
    """Test ChoiceEvaluator."""
    evaluator = ChoiceEvaluator()
    
    predictions = [
        "The answer is A",
        "B",
        "I think it's C",
        "(D)",
    ]
    references = ["A", "B", "C", "A"]
    
    result = evaluator.compute(predictions, references)
    
    assert "accuracy" in result.metrics
    assert "choice_accuracy" in result.metrics
    assert "bias_score" in result.metrics
    
    assert result.metrics["accuracy"] == 0.75
    
    assert len(result.details) == 4
    assert result.details[0]["extracted_answer"] == "A"
    assert result.details[0]["correct"] is True
    assert result.details[3]["extracted_answer"] == "D"
    assert result.details[3]["correct"] is False
    
    print("✓ test_choice_evaluator passed")


def test_option_bias():
    """Test option bias analysis."""
    predictions = ["A", "A", "A", "A", "B"]
    references = ["A", "B", "C", "D", "A"]
    
    bias = compute_option_bias(predictions, references)
    
    assert "prediction_distribution" in bias
    assert "reference_distribution" in bias
    assert "per_option_accuracy" in bias
    assert "bias_score" in bias
    
    assert bias["prediction_distribution"]["A"] == 0.8
    assert bias["prediction_distribution"]["B"] == 0.2
    
    assert bias["bias_score"] > 0
    
    print("✓ test_option_bias passed")


def test_choice_evaluator_invalid_answers():
    """Test ChoiceEvaluator with invalid/unparseable answers."""
    evaluator = ChoiceEvaluator()
    
    predictions = [
        "I don't know",
        "Maybe X or Y",
        "A",
    ]
    references = ["A", "B", "A"]
    
    result = evaluator.compute(predictions, references)
    
    assert result.metrics["invalid_rate"] > 0
    assert result.details[0]["extracted_answer"] is None
    assert result.details[2]["correct"] is True
    
    print("✓ test_choice_evaluator_invalid_answers passed")


def test_evaluator_validation():
    """Test input validation."""
    evaluator = TextEvaluator()
    
    try:
        evaluator.compute(["a", "b"], ["a"])
        assert False, "Should raise ValueError"
    except ValueError as e:
        assert "Length mismatch" in str(e)
    
    try:
        evaluator.compute([], [])
        assert False, "Should raise ValueError"
    except ValueError as e:
        assert "Empty input" in str(e)
    
    print("✓ test_evaluator_validation passed")


def run_all_tests():
    """Run all tests."""
    print("=" * 50)
    print("Running evaluators tests...")
    print("=" * 50)
    
    test_evaluation_result()
    test_text_evaluator()
    test_text_evaluator_perfect_match()
    test_extract_choice()
    test_extract_choice_english_statements()
    test_extract_choice_chinese()
    test_extract_choice_negation()
    test_extract_choice_uncertainty()
    test_extract_choice_cot()
    test_choice_evaluator()
    test_option_bias()
    test_choice_evaluator_invalid_answers()
    test_evaluator_validation()
    
    print("=" * 50)
    print("All tests passed!")
    print("=" * 50)


if __name__ == "__main__":
    run_all_tests()
