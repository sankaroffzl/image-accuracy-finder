# Batch Comparison Mode Design

## Overview
Add batch comparison to the Image Accuracy Finder: upload 1 reference image + 50+ candidate images, compare all candidates against the reference, and display a ranked list from most to least similar.

## Architecture

### New Endpoint
- **`POST /compare-batch`** — Accepts one reference file + multiple candidate files
- Returns sorted JSON array with overall score per candidate

### Data Flow
1. Frontend sends reference + candidates as `multipart/form-data`
2. Flask saves all files to a temp batch directory
3. Loops through candidates, calling existing orchestrator for each
4. Sorts results by score descending
5. Cleans up all temp files
6. Returns JSON results → frontend renders ranked table

### Reuse
- No changes to individual engine modules (SSIM, ORB, Histogram, pHash)
- Orchestrator's `compare_images` reused as-is
- Existing error handling patterns reused

## Frontend

### Upload Page Updates (`index.html`)
- Two dropzones: Reference (single image) and Candidates (multiple images)
- Reference shows one preview; Candidates shows a file count badge
- "Compare All" button (enabled when 1 reference + ≥1 candidate)
- Loading spinner with status text ("Comparing 50 images...")

### Results Page (`results.html` or new `batch_results.html`)
- Ranked table: rank, thumbnail, filename, overall score (with color bar), breakdown toggle
- Pagination (20 per page) for 50+ results
- Click row to expand algorithm breakdown
- Sort by rank (default) or name
- Back button to upload more

## Implementation Plan

1. Update orchestrator with `batch_compare` helper
2. Add `/compare-batch` route + validation
3. Update upload page (two dropzones)
4. Create batch results page (ranked table)
5. Update tests
6. Verify existing tests still pass
