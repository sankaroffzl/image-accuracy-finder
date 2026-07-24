import numpy as np
import pytest
from engine.feature_matcher import compute_orb_match


def test_identical_images_high_score():
    img = np.random.randint(0, 256, (200, 200), dtype=np.uint8)
    score = compute_orb_match(img, img)
    assert score >= 0.8


def test_blank_vs_blank_returns_0():
    img_a = np.zeros((100, 100), dtype=np.uint8)
    img_b = np.zeros((100, 100), dtype=np.uint8)
    score = compute_orb_match(img_a, img_b)
    assert 0.0 <= score <= 1.0


def test_completely_different_images():
    img_a = np.zeros((100, 100), dtype=np.uint8)
    img_b = np.ones((100, 100), dtype=np.uint8) * 255
    score = compute_orb_match(img_a, img_b)
    assert 0.0 <= score <= 1.0


def test_color_image_conversion():
    img_a = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
    img_b = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
    score = compute_orb_match(img_a, img_b)
    assert 0.0 <= score <= 1.0
