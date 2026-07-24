import numpy as np
import pytest
from engine.histogram import compute_histogram_similarity


def test_identical_images_return_1_0():
    img = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
    score = compute_histogram_similarity(img, img)
    assert score == pytest.approx(1.0, abs=0.01)


def test_opposite_colors_low_score():
    img_a = np.zeros((100, 100, 3), dtype=np.uint8)       # all black
    img_b = np.ones((100, 100, 3), dtype=np.uint8) * 255    # all white
    score = compute_histogram_similarity(img_a, img_b)
    assert score < 0.5


def test_grayscale_input():
    img_a = np.zeros((100, 100), dtype=np.uint8)
    img_b = np.ones((100, 100), dtype=np.uint8) * 128
    score = compute_histogram_similarity(img_a, img_b)
    assert 0.0 <= score <= 1.0


def test_score_range():
    img_a = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
    img_b = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
    score = compute_histogram_similarity(img_a, img_b)
    assert 0.0 <= score <= 1.0
