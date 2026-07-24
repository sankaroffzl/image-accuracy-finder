"""Orchestrates all image comparison algorithms into a single score."""

import os
import cv2
import numpy as np
from PIL import Image
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
    """Load image safely using PIL, resize to max dims, return uint8 RGB array.
    
    Uses PIL for loading because OpenCV's imread can segfault on corrupted
    or unusual image files, killing the entire server process.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    # PIL is crash-safe — it won't segfault on bad images
    try:
        pil_img = Image.open(image_path)
        pil_img.verify()  # Quick check without decoding pixels
        pil_img = Image.open(image_path)  # Re-open after verify
        pil_img = pil_img.convert("RGB")  # Safe: RGBA/CMYK/P → RGB
    except Exception as e:
        raise ValueError(f"Cannot decode image {os.path.basename(image_path)}: {e}")

    img = np.array(pil_img, dtype=np.uint8)

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

        # Run all algorithms (each wrapped to isolate crashes)
        ssim_score = 0.0
        orb_score = 0.0
        hist_score = 0.0
        phash_score = 0.0
        try:
            ssim_score = compute_ssim(gray_a, gray_b)
        except Exception:
            pass  # SSIM failed, continue with other algorithms
        try:
            orb_score = compute_orb_match(gray_a, gray_b)
        except Exception:
            pass  # ORB failed, continue
        try:
            hist_score = compute_histogram_similarity(img_a, img_b)
        except Exception:
            pass  # Histogram failed, continue
        try:
            phash_score = compute_phash_similarity(img_a, img_b)
        except Exception:
            pass  # pHash failed, continue

        # Compute weighted overall score (convert to percentage)
        overall = (
            ssim_score * WEIGHTS["ssim"]
            + orb_score * WEIGHTS["orb"]
            + hist_score * WEIGHTS["histogram"]
            + phash_score * WEIGHTS["phash"]
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

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


def batch_compare(ref_path: str, candidate_paths: list[str]) -> dict:
    """Compare multiple candidates against one reference image.
    
    Args:
        ref_path: Path to reference image
        candidate_paths: List of paths to candidate images
    
    Returns:
        Dict with:
          - results: list of result dicts sorted by overall score descending
          - total: total number of candidates attempted
          - failed: number of candidates that failed processing
        Each result dict contains all compare_images fields plus 'filename' and '_path'.
    """
    results = []
    failed = 0
    for path in candidate_paths:
        result = compare_images(ref_path, path)
        if not result.get("success", False):
            failed += 1
            continue  # Skip failed comparisons
        result["filename"] = os.path.basename(path)
        result["_path"] = path
        results.append(result)

    results.sort(key=lambda r: r.get("overall", 0), reverse=True)
    return {"results": results, "total": len(candidate_paths), "failed": failed}
