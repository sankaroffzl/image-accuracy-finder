import numpy as np
import tempfile
import os
import cv2
from PIL import Image
import pytest
from engine.orchestrator import compare_images, batch_compare


def _create_test_array(gray_value=128, size=(100, 100)):
    return np.full((*size, 3), gray_value, dtype=np.uint8)


def _create_test_image(path, color=None):
    """Create a test image. If color is None, uses random noise (has features)."""
    if color is None:
        arr = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
    else:
        arr = np.ones((100, 100, 3), dtype=np.uint8) * color
    img = Image.fromarray(arr)
    img.save(path)


def test_identical_images_high_score():
    with tempfile.TemporaryDirectory() as tmp:
        path_a = os.path.join(tmp, "a.png")
        path_b = os.path.join(tmp, "b.png")
        # Use random noise images with detectable features
        np.random.seed(42)
        _create_test_image(path_a)
        np.random.seed(42)
        _create_test_image(path_b)
        result = compare_images(path_a, path_b)
        assert result["success"] is True
        assert 0.0 <= result["overall"] <= 100.0
        assert result["overall"] > 80.0  # identical should be high


def test_different_images_lower_score():
    with tempfile.TemporaryDirectory() as tmp:
        path_a = os.path.join(tmp, "a.png")
        path_b = os.path.join(tmp, "b.png")
        _create_test_image(path_a, 0)      # black
        _create_test_image(path_b, 255)    # white
        result = compare_images(path_a, path_b)
        assert result["success"] is True
        assert result["overall"] < 50.0


def test_result_structure():
    with tempfile.TemporaryDirectory() as tmp:
        path_a = os.path.join(tmp, "a.png")
        path_b = os.path.join(tmp, "b.png")
        _create_test_image(path_a, 100)
        _create_test_image(path_b, 100)
        result = compare_images(path_a, path_b)
        assert "success" in result
        assert "overall" in result
        assert "verdict" in result
        assert "details" in result
        assert "ssim" in result["details"]
        assert "orb" in result["details"]
        assert "histogram" in result["details"]
        assert "phash" in result["details"]


def test_nonexistent_file_returns_error():
    result = compare_images("/nonexistent/a.png", "/nonexistent/b.png")
    assert result["success"] is False
    assert "error" in result


def test_batch_compare_returns_sorted_results():
    with tempfile.TemporaryDirectory() as tmp:
        ref_path = os.path.join(tmp, "ref.png")
        cv2.imwrite(ref_path, cv2.cvtColor(_create_test_array(200), cv2.COLOR_RGB2BGR))
        candidate_paths = []
        for val in [200, 100, 200]:
            p = os.path.join(tmp, f"c{val}.png")
            cv2.imwrite(p, cv2.cvtColor(_create_test_array(val), cv2.COLOR_RGB2BGR))
            candidate_paths.append(p)
        results = batch_compare(ref_path, candidate_paths)
        assert len(results) == 3
        for i in range(len(results) - 1):
            assert results[i]["overall"] >= results[i + 1]["overall"]


def test_batch_compare_single_candidate():
    with tempfile.TemporaryDirectory() as tmp:
        ref_path = os.path.join(tmp, "ref.png")
        cv2.imwrite(ref_path, cv2.cvtColor(_create_test_array(200), cv2.COLOR_RGB2BGR))
        cand_path = os.path.join(tmp, "cand.png")
        cv2.imwrite(cand_path, cv2.cvtColor(_create_test_array(200), cv2.COLOR_RGB2BGR))
        results = batch_compare(ref_path, [cand_path])
        assert len(results) == 1
        assert "filename" in results[0]


def test_batch_compare_adds_filename():
    with tempfile.TemporaryDirectory() as tmp:
        ref_path = os.path.join(tmp, "ref.jpg")
        cv2.imwrite(ref_path, cv2.cvtColor(_create_test_array(200), cv2.COLOR_RGB2BGR))
        cand_path = os.path.join(tmp, "candidate.jpg")
        cv2.imwrite(cand_path, cv2.cvtColor(_create_test_array(100), cv2.COLOR_RGB2BGR))
        results = batch_compare(ref_path, [cand_path])
        assert results[0]["filename"] == "candidate.jpg"
