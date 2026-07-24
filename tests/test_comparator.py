import numpy as np
import pytest
from engine.comparator import compute_ssim


def test_identical_images_return_1_0():
    img = np.random.randint(0, 256, (100, 100), dtype=np.uint8)
    score = compute_ssim(img, img)
    assert score == pytest.approx(1.0, abs=0.01)


def test_completely_different_images_return_low_score():
    img_a = np.zeros((100, 100), dtype=np.uint8)
    img_b = np.ones((100, 100), dtype=np.uint8) * 255
    score = compute_ssim(img_a, img_b)
    assert score < 0.1


def test_ssim_raises_on_dimension_mismatch():
    img_a = np.zeros((100, 100), dtype=np.uint8)
    img_b = np.zeros((200, 200), dtype=np.uint8)
    with pytest.raises(ValueError, match="dimensions"):
        compute_ssim(img_a, img_b)


def test_color_image_conversion():
    from engine.comparator import compute_ssim
    img_a = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
    img_b = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
    score = compute_ssim(img_a, img_b)
    assert 0.0 <= score <= 1.0
