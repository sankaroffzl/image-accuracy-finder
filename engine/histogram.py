"""Histogram-based image comparison using OpenCV."""

import cv2
import numpy as np


def compute_histogram_similarity(image_a: np.ndarray, image_b: np.ndarray) -> float:
    """Compare two images using histogram correlation.

    Args:
        image_a: First image as numpy array.
        image_b: Second image as numpy array.

    Returns:
        Float between 0.0 and 1.0, higher = more similar color distribution.
    """
    # Ensure 3-channel (RGB)
    if image_a.ndim == 2:
        image_a = cv2.cvtColor(image_a, cv2.COLOR_GRAY2RGB)
    if image_b.ndim == 2:
        image_b = cv2.cvtColor(image_b, cv2.COLOR_GRAY2RGB)

    scores = []
    for channel in range(3):
        hist_a = cv2.calcHist([image_a], [channel], None, [256], [0, 256])
        hist_b = cv2.calcHist([image_b], [channel], None, [256], [0, 256])
        cv2.normalize(hist_a, hist_a, 0, 1, cv2.NORM_MINMAX)
        cv2.normalize(hist_b, hist_b, 0, 1, cv2.NORM_MINMAX)
        corr = cv2.compareHist(hist_a, hist_b, cv2.HISTCMP_CORREL)
        scores.append(max(0.0, corr))  # Clip negative correlation to 0

    return float(np.mean(scores))
