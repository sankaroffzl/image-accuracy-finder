import numpy as np
import tempfile
import os
from PIL import Image
import pytest
from engine.orchestrator import compare_images


def _create_test_image(path, color=128):
    arr = np.ones((100, 100, 3), dtype=np.uint8) * color
    img = Image.fromarray(arr)
    img.save(path)


def test_identical_images_high_score():
    with tempfile.TemporaryDirectory() as tmp:
        path_a = os.path.join(tmp, "a.png")
        path_b = os.path.join(tmp, "b.png")
        _create_test_image(path_a, 200)
        _create_test_image(path_b, 200)
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
