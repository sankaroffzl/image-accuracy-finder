"""ORB feature-based image matching using OpenCV."""

import cv2
import numpy as np


def compute_orb_match(image_a: np.ndarray, image_b: np.ndarray) -> float:
    """Compute feature matching score between two images using ORB.

    Args:
        image_a: First image as numpy array (grayscale or RGB).
        image_b: Second image as numpy array (grayscale or RGB).

    Returns:
        Float between 0.0 and 1.0, higher = more feature matches.
    """
    # Convert to grayscale if needed
    if image_a.ndim == 3:
        image_a = cv2.cvtColor(image_a, cv2.COLOR_RGB2GRAY)
    if image_b.ndim == 3:
        image_b = cv2.cvtColor(image_b, cv2.COLOR_RGB2GRAY)

    orb = cv2.ORB_create(nfeatures=1000)
    kp_a, des_a = orb.detectAndCompute(image_a, None)
    kp_b, des_b = orb.detectAndCompute(image_b, None)

    if des_a is None or des_b is None or len(kp_a) < 2 or len(kp_b) < 2:
        return 0.0

    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
    matches = bf.knnMatch(des_a, des_b, k=2)

    # Ratio test as per Lowe's paper
    good_matches = []
    for match_pair in matches:
        if len(match_pair) == 2:
            m, n = match_pair
            if m.distance < 0.75 * n.distance:
                good_matches.append(m)

    total_keypoints = max(len(kp_a), len(kp_b))
    if total_keypoints == 0:
        return 0.0

    score = len(good_matches) / total_keypoints
    return float(np.clip(score, 0.0, 1.0))
