import numpy as np
from skimage.metrics import structural_similarity as ssim


def compute_ssim(image_a: np.ndarray, image_b: np.ndarray) -> float:
    if image_a.ndim == 3:
        image_a = np.mean(image_a, axis=2).astype(np.uint8)
    if image_b.ndim == 3:
        image_b = np.mean(image_b, axis=2).astype(np.uint8)

    if image_a.shape != image_b.shape:
        raise ValueError(
            f"Image dimensions must match: {image_a.shape} vs {image_b.shape}"
        )

    score, _ = ssim(image_a, image_b, full=True, data_range=255)
    return float(np.clip(score, 0.0, 1.0))
