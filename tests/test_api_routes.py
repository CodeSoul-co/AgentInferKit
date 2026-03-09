"""
Unit tests for API routes.

Run with: python -m pytest tests/test_api_routes.py -v
Or directly: python tests/test_api_routes.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_imports():
    """Test that all API modules can be imported."""
    from api import datasets_router, results_router, chat_router
    from api.schemas import (
        ResponseEnvelope,
        DatasetUploadResponse,
        DatasetListResponse,
        SamplePreviewResponse,
        DatasetStatsResponse,
        MetricsResponse,
        PredictionListResponse,
        CompareRequest,
        CompareResponse,
        ChatCompleteRequest,
        ChatCompleteResponse,
    )
    
    assert datasets_router is not None
    assert results_router is not None
    assert chat_router is not None
    
    print("✓ test_imports passed")


def test_router_prefixes():
    """Test that routers have correct prefixes."""
    from api import datasets_router, results_router, chat_router
    
    assert datasets_router.prefix == "/datasets"
    assert results_router.prefix == "/results"
    assert chat_router.prefix == "/chat"
    
    print("✓ test_router_prefixes passed")


def test_router_routes():
    """Test that routers have expected routes."""
    from api import datasets_router, results_router, chat_router
    
    datasets_paths = [r.path for r in datasets_router.routes]
    assert "/datasets/upload" in datasets_paths
    assert "/datasets" in datasets_paths  # list endpoint
    assert "/datasets/{dataset_id}/preview" in datasets_paths
    assert "/datasets/{dataset_id}/stats" in datasets_paths
    assert "/datasets/{dataset_id}" in datasets_paths  # delete endpoint
    
    results_paths = [r.path for r in results_router.routes]
    assert "/results/{experiment_id}/metrics" in results_paths
    assert "/results/{experiment_id}/predictions" in results_paths
    assert "/results/compare" in results_paths
    assert "/results/{experiment_id}/export" in results_paths
    
    chat_paths = [r.path for r in chat_router.routes]
    assert "/chat/complete" in chat_paths
    assert "/chat/stream" in chat_paths
    
    print("✓ test_router_routes passed")


def test_response_envelope():
    """Test ResponseEnvelope model."""
    from api.schemas import ResponseEnvelope
    
    envelope = ResponseEnvelope(
        code=0,
        message="ok",
        data={"test": "value"}
    )
    
    assert envelope.code == 0
    assert envelope.message == "ok"
    assert envelope.data == {"test": "value"}
    
    error_envelope = ResponseEnvelope(
        code=400,
        message="Bad request",
        data=None
    )
    
    assert error_envelope.code == 400
    
    print("✓ test_response_envelope passed")


def run_all_tests():
    """Run all tests."""
    print("=" * 50)
    print("Running API routes tests...")
    print("=" * 50)
    
    test_imports()
    test_router_prefixes()
    test_router_routes()
    test_response_envelope()
    
    print("=" * 50)
    print("All tests passed!")
    print("=" * 50)


if __name__ == "__main__":
    run_all_tests()
