"""Perceptual hash-based image comparison using imagehash."""

import numpy as np
from PIL import Image
import imagehash


def compute_phash_similarity(image_a: np.ndarray, image_b: np.ndarray) -> float:
    """Compare two images using perceptual hashing.

    Args:
        image_a: First image as numpy array.
        image_b: Second image as numpy array.

    Returns:
        Float between 0.0 and 1.0, higher = more similar.
    """
    pil_a = Image.fromarray(image_a)
    pil_b = Image.fromarray(image_b)

    hash_a = imagehash.phash(pil_a)
    hash_b = imagehash.phash(pil_b)

    hamming_distance = hash_a - hash_b  # Hamming distance
    max_distance = len(hash_a.hash) ** 2  # max possible distance

    similarity = 1.0 - (hamming_distance / max_distance)
    return float(np.clip(similarity, 0.0, 1.0))
