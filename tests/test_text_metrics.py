"""
Unit tests for text_metrics.py

Run with: python -m pytest tests/test_text_metrics.py -v
Or directly: python tests/test_text_metrics.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from evaluators.text_metrics import (
    normalize_text,
    exact_match,
    accuracy,
    f1_score,
    rouge_l,
    rouge_l_f1,
    bleu,
    compute_all_metrics,
)


def test_normalize_text():
    """Test text normalization."""
    assert normalize_text("Hello, World!") == "hello world"
    assert normalize_text("  Multiple   Spaces  ") == "multiple spaces"
    assert normalize_text("UPPERCASE") == "uppercase"
    assert normalize_text("test123") == "test123"
    assert normalize_text("") == ""
    print("✓ test_normalize_text passed")


def test_exact_match():
    """Test exact match function."""
    assert exact_match("hello", "hello") is True
    assert exact_match("Hello", "hello") is True
    assert exact_match("hello world", "hello world") is True
    assert exact_match("hello", "world") is False
    assert exact_match("Hello, World!", "hello world", normalize=True) is True
    assert exact_match("Hello", "hello", normalize=False) is False
    print("✓ test_exact_match passed")


def test_accuracy():
    """Test accuracy computation."""
    preds = ["A", "B", "C", "D"]
    gts = ["A", "B", "X", "Y"]
    assert accuracy(preds, gts) == 0.5
    
    assert accuracy(["a"], ["A"]) == 1.0
    assert accuracy(["a"], ["b"]) == 0.0
    assert accuracy([], []) == 0.0
    
    try:
        accuracy(["a"], ["a", "b"])
        assert False, "Should raise ValueError"
    except ValueError:
        pass
    
    print("✓ test_accuracy passed")


def test_f1_score():
    """Test F1 score computation."""
    assert f1_score("the cat sat", "the cat sat") == 1.0
    
    assert f1_score("the cat", "the cat sat") < 1.0
    assert f1_score("the cat", "the cat sat") > 0.0
    
    f1 = f1_score("the cat", "the cat sat on the mat")
    assert 0 < f1 < 1
    
    assert f1_score("apple", "orange") == 0.0
    
    assert f1_score("", "") == 1.0
    assert f1_score("hello", "") == 0.0
    assert f1_score("", "hello") == 0.0
    
    print("✓ test_f1_score passed")


def test_rouge_l():
    """Test ROUGE-L computation."""
    p, r, f1 = rouge_l("the cat sat", "the cat sat")
    assert p == 1.0
    assert r == 1.0
    assert f1 == 1.0
    
    p, r, f1 = rouge_l("the cat", "the cat sat on mat")
    assert 0 < p <= 1
    assert 0 < r < 1
    assert 0 < f1 < 1
    
    p, r, f1 = rouge_l("apple banana", "orange grape")
    assert p == 0.0
    assert r == 0.0
    assert f1 == 0.0
    
    p, r, f1 = rouge_l("", "")
    assert f1 == 1.0
    
    print("✓ test_rouge_l passed")


def test_rouge_l_f1():
    """Test ROUGE-L F1 convenience function."""
    assert rouge_l_f1("hello world", "hello world") == 1.0
    assert rouge_l_f1("hello", "world") == 0.0
    assert 0 < rouge_l_f1("hello world", "hello there world") < 1
    print("✓ test_rouge_l_f1 passed")


def test_bleu():
    """Test BLEU score computation."""
    assert bleu("the cat sat on the mat", "the cat sat on the mat") == 1.0
    
    score = bleu("the cat", "the cat sat on the mat")
    assert 0 <= score <= 1
    
    assert bleu("apple banana cherry", "orange grape lemon") == 0.0
    
    assert bleu("", "hello") == 0.0
    assert bleu("hello", "") == 0.0
    
    print("✓ test_bleu passed")


def test_compute_all_metrics():
    """Test combined metrics computation."""
    metrics = compute_all_metrics("the cat sat", "the cat sat")
    
    assert "exact_match" in metrics
    assert "f1" in metrics
    assert "rouge_l_f1" in metrics
    assert "bleu" in metrics
    
    assert metrics["exact_match"] is True
    assert metrics["f1"] == 1.0
    assert metrics["rouge_l_f1"] == 1.0
    assert metrics["bleu"] > 0.99  # Allow for floating point precision
    
    metrics2 = compute_all_metrics("hello", "world")
    assert metrics2["exact_match"] is False
    assert metrics2["f1"] == 0.0
    
    print("✓ test_compute_all_metrics passed")


def run_all_tests():
    """Run all tests."""
    print("=" * 50)
    print("Running text_metrics tests...")
    print("=" * 50)
    
    test_normalize_text()
    test_exact_match()
    test_accuracy()
    test_f1_score()
    test_rouge_l()
    test_rouge_l_f1()
    test_bleu()
    test_compute_all_metrics()
    
    print("=" * 50)
    print("All tests passed!")
    print("=" * 50)


if __name__ == "__main__":
    run_all_tests()
