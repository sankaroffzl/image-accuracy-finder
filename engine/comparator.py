"""SSIM-based image comparison using scikit-image."""

import numpy as np
from skimage.metrics import structural_similarity as ssim


def compute_ssim(image_a: np.ndarray, image_b: np.ndarray) -> float:
    """Compute Structural Similarity Index between two images.

    Args:
        image_a: First image as numpy array (grayscale H×W or RGB H×W×C).
        image_b: Second image as numpy array (grayscale H×W or RGB H×W×C).

    Returns:
        Float between 0.0 and 1.0, higher = more similar.

    Raises:
        ValueError: If image dimensions differ by more than 10%.
    """
    # Convert to grayscale if needed
    if image_a.ndim == 3:
        image_a = np.mean(image_a, axis=2).astype(np.uint8)
    if image_b.ndim == 3:
        image_b = np.mean(image_b, axis=2).astype(np.uint8)

    # Check dimension tolerance (allow up to 10% difference)
    shape_a, shape_b = image_a.shape, image_b.shape
    if shape_a != shape_b:
        h_ratio = min(shape_a[0], shape_b[0]) / max(shape_a[0], shape_b[0])
        w_ratio = min(shape_a[1], shape_b[1]) / max(shape_a[1], shape_b[1])
        if h_ratio < 0.9 or w_ratio < 0.9:
            raise ValueError(
                f"Image dimensions differ by more than 10%: "
                f"{shape_a} vs {shape_b}"
            )

    score, _ = ssim(image_a, image_b, full=True, data_range=255)
    return float(np.clip(score, 0.0, 1.0))
