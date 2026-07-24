"""Orchestrates all image comparison algorithms into a single score."""

import os
import cv2
import numpy as np
from engine.comparator import compute_ssim
from engine.feature_matcher import compute_orb_match
from engine.histogram import compute_histogram_similarity
from engine.hasher import compute_phash_similarity

# Weights for each algorithm
WEIGHTS = {
    "ssim": 0.35,
    "orb": 0.30,
    "histogram": 0.25,
    "phash": 0.10,
}

MAX_IMAGE_DIM = (800, 800)


def _load_and_preprocess(image_path: str) -> np.ndarray:
    """Load image with OpenCV, resize to max dims, return RGB array."""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not decode image: {image_path}")

    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # Resize if larger than MAX_IMAGE_DIM while maintaining aspect ratio
    h, w = img.shape[:2]
    if h > MAX_IMAGE_DIM[1] or w > MAX_IMAGE_DIM[0]:
        scale = min(MAX_IMAGE_DIM[0] / w, MAX_IMAGE_DIM[1] / h)
        new_w, new_h = int(w * scale), int(h * scale)
        img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

    return img


def _ensure_same_size(img_a: np.ndarray, img_b: np.ndarray) -> tuple:
    """Resize both images to the same dimensions (min of each dimension)."""
    h = min(img_a.shape[0], img_b.shape[0])
    w = min(img_a.shape[1], img_b.shape[1])
    img_a = cv2.resize(img_a, (w, h), interpolation=cv2.INTER_AREA)
    img_b = cv2.resize(img_b, (w, h), interpolation=cv2.INTER_AREA)
    return img_a, img_b


def compare_images(image_a_path: str, image_b_path: str) -> dict:
    """Compare two images using all algorithms and return a weighted score.

    Args:
        image_a_path: Path to the first image file.
        image_b_path: Path to the second image file.

    Returns:
        dict with keys: success, overall (0-100), verdict, details
    """
    try:
        # Load images
        img_a = _load_and_preprocess(image_a_path)
        img_b = _load_and_preprocess(image_b_path)

        # Ensure same size
        img_a, img_b = _ensure_same_size(img_a, img_b)

        # Grayscale versions for SSIM and ORB
        gray_a = cv2.cvtColor(img_a, cv2.COLOR_RGB2GRAY)
        gray_b = cv2.cvtColor(img_b, cv2.COLOR_RGB2GRAY)

        # Run all algorithms
        ssim_score = compute_ssim(gray_a, gray_b)
        orb_score = compute_orb_match(gray_a, gray_b)
        hist_score = compute_histogram_similarity(img_a, img_b)
        phash_score = compute_phash_similarity(img_a, img_b)

        # Compute weighted overall score (convert to percentage)
        # If ORB returns 0.0 but SSIM indicates near-identical images,
        # ORB likely failed due to lack of features — redistribute its weight
        if orb_score == 0.0 and ssim_score > 0.95:
            remaining = {k: v for k, v in WEIGHTS.items() if k != "orb"}
            total_remaining = sum(remaining.values())
            orb_weight = 0.0
            ssim_weight = WEIGHTS["ssim"] / total_remaining
            hist_weight = WEIGHTS["histogram"] / total_remaining
            phash_weight = WEIGHTS["phash"] / total_remaining
        else:
            ssim_weight = WEIGHTS["ssim"]
            orb_weight = WEIGHTS["orb"]
            hist_weight = WEIGHTS["histogram"]
            phash_weight = WEIGHTS["phash"]

        overall = (
            ssim_score * ssim_weight
            + orb_score * orb_weight
            + hist_score * hist_weight
            + phash_score * phash_weight
        ) * 100.0

        overall = round(float(np.clip(overall, 0.0, 100.0)), 1)

        # Verdict
        if overall >= 75.0:
            verdict = "high_match"
        elif overall >= 50.0:
            verdict = "moderate_match"
        else:
            verdict = "low_match"

        return {
            "success": True,
            "overall": overall,
            "verdict": verdict,
            "details": {
                "ssim": round(float(ssim_score), 4),
                "orb": round(float(orb_score), 4),
                "histogram": round(float(hist_score), 4),
                "phash": round(float(phash_score), 4),
            },
        }

    except (FileNotFoundError, ValueError, Exception) as e:
        return {
            "success": False,
            "error": str(e),
        }
