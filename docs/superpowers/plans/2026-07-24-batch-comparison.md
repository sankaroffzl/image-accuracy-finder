# Batch Comparison Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add batch comparison feature — upload 1 reference image + 50+ candidates, get ranked results.

**Architecture:** Reuses existing orchestrator's `compare_images` in a loop. New `/compare-batch` endpoint returns sorted JSON. Frontend gets two dropzones (reference + candidates) and a ranked results table with pagination.

**Tech Stack:** Flask, scikit-image, OpenCV, imagehash, Pillow, numpy, gunicorn

## Global Constraints

- Python 3.8+ required
- Keep dependencies minimal — only Flask, opencv-python, scikit-image, Pillow, imagehash, numpy
- All existing tests must remain passing
- Follow existing patterns (same file structure, naming conventions, error handling)
- File uploads cleaned up in `finally` block

---

### Task 1: Orchestrator batch_compare

**Files:**
- Modify: `engine/orchestrator.py` (add `batch_compare` function)
- Test: `tests/test_orchestrator.py` (add 3 batch tests)

**Interfaces:**
- Consumes: `orchestrator.compare_images(ref_path, candidate_path)` — returns dict with `overall`, `ssim`, `orb`, `histogram`, `phash`, `verdict`
- Produces: `orchestrator.batch_compare(ref_path, candidate_paths)` — returns list of dicts sorted by `overall` descending

- [ ] **Step 1: Write the failing tests**

```python
def test_batch_compare_returns_sorted_results():
    ref = _create_test_image(200)
    candidates = [_create_test_image(200), _create_test_image(100), _create_test_image(200)]
    results = batch_compare(ref, candidates)
    assert len(results) == 3
    # Check sorted descending
    for i in range(len(results) - 1):
        assert results[i]["overall"] >= results[i + 1]["overall"]

def test_batch_compare_single_candidate():
    ref = _create_test_image(200)
    candidate = _create_test_image(200)
    results = batch_compare(ref, [candidate])
    assert len(results) == 1
    assert "filename" in results[0]

def test_batch_compare_adds_filename():
    ref = _create_test_image(200)
    candidates = [_create_test_image(100)]
    # Use a tempfile path to test filename extraction
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        cv2.imwrite(f.name, candidates[0])
        path = f.name
    results = batch_compare(ref, [path])
    assert results[0]["filename"] == os.path.basename(path)
    os.unlink(path)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_orchestrator.py::test_batch_compare_returns_sorted_results tests/test_orchestrator.py::test_batch_compare_single_candidate tests/test_orchestrator.py::test_batch_compare_adds_filename -v`

Expected: FAIL — `batch_compare` not defined

- [ ] **Step 3: Add batch_compare to orchestrator**

Add at end of `engine/orchestrator.py`:

```python
def batch_compare(ref_path: str, candidate_paths: list[str]) -> list[dict]:
    """Compare multiple candidates against one reference image.
    
    Args:
        ref_path: Path to reference image
        candidate_paths: List of paths to candidate images
    
    Returns:
        List of result dicts sorted by overall score descending,
        each containing all compare_images fields plus 'filename'
    """
    results = []
    for path in candidate_paths:
        result = compare_images(ref_path, path)
        result["filename"] = os.path.basename(path)
        results.append(result)
    
    results.sort(key=lambda r: r["overall"], reverse=True)
    return results
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_orchestrator.py::test_batch_compare_returns_sorted_results tests/test_orchestrator.py::test_batch_compare_single_candidate tests/test_orchestrator.py::test_batch_compare_adds_filename -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add engine/orchestrator.py tests/test_orchestrator.py
git commit -m "feat: add batch_compare to orchestrator"
```

---

### Task 2: Batch API route

**Files:**
- Modify: `app.py` (add `/compare-batch` route)
- Test: `tests/test_app.py` (add batch endpoint tests)
- Create: `static/uploads/` (for batch temp files, or reuse uploads/)

**Interfaces:**
- Consumes: `orchestrator.batch_compare(ref_path, candidate_paths)` from Task 1
- Produces: JSON with `results` (list), `count` (int), `success` (bool)

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_app.py`:

```python
class TestBatchCompare:
    def setup_method(self):
        self.ref = cv2.imencode('.jpg', np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8))[1].tobytes()
        self.candidate = cv2.imencode('.jpg', np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8))[1].tobytes()

    def test_batch_compare_success(self, app):
        """Test batch compare endpoint returns sorted results."""
        with app.test_client() as client:
            data = {
                'reference': (io.BytesIO(self.ref), 'ref.jpg'),
                'candidates': [
                    (io.BytesIO(self.candidate), 'cand1.jpg'),
                    (io.BytesIO(self.candidate), 'cand2.jpg'),
                ]
            }
            resp = client.post('/compare-batch', data=data, content_type='multipart/form-data')
            assert resp.status_code == 200
            json_data = resp.get_json()
            assert json_data['success'] is True
            assert json_data['count'] == 2
            assert len(json_data['results']) == 2

    def test_batch_compare_missing_reference(self, app):
        """Test batch compare fails without reference."""
        with app.test_client() as client:
            data = {
                'candidates': [(io.BytesIO(self.candidate), 'cand1.jpg')]
            }
            resp = client.post('/compare-batch', data=data, content_type='multipart/form-data')
            assert resp.status_code == 400

    def test_batch_compare_no_candidates(self, app):
        """Test batch compare fails without candidates."""
        with app.test_client() as client:
            data = {
                'reference': (io.BytesIO(self.ref), 'ref.jpg'),
            }
            resp = client.post('/compare-batch', data=data, content_type='multipart/form-data')
            assert resp.status_code == 400

    def test_batch_compare_invalid_file_type(self, app):
        """Test batch compare rejects invalid file types."""
        with app.test_client() as client:
            data = {
                'reference': (io.BytesIO(self.ref), 'ref.jpg'),
                'candidates': [(io.BytesIO(b'not an image'), 'bad.txt')]
            }
            resp = client.post('/compare-batch', data=data, content_type='multipart/form-data')
            assert resp.status_code == 400
```

Also need to add `np` and `io` imports at top of test_app.py:
```python
import numpy as np
import io
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_app.py::TestBatchCompare -v`

Expected: FAIL — 404 (no route yet)

- [ ] **Step 3: Add /compare-batch route to app.py**

Add before the existing `/compare` route:

```python
@app.route('/compare-batch', methods=['POST'])
def compare_batch():
    """Compare multiple candidate images against a single reference."""
    if 'reference' not in request.files:
        return jsonify(success=False, error='No reference image provided'), 400
    
    if 'candidates' not in request.files:
        return jsonify(success=False, error='No candidate images provided'), 400
    
    ref_file = request.files['reference']
    if ref_file.filename == '' or not _allowed_file(ref_file.filename):
        return jsonify(success=False, error='Invalid reference file'), 400
    
    candidate_files = request.files.getlist('candidates')
    valid_candidates = [f for f in candidate_files if f.filename != '' and _allowed_file(f.filename)]
    
    if not valid_candidates:
        return jsonify(success=False, error='No valid candidate images provided'), 400
    
    batch_dir = os.path.join(app.instance_path, 'batch_uploads')
    os.makedirs(batch_dir, exist_ok=True)
    
    try:
        # Save reference
        ref_ext = _get_ext(ref_file.filename)
        ref_path = os.path.join(batch_dir, f'ref_{uuid.uuid4().hex}{ref_ext}')
        ref_file.save(ref_path)
        
        # Save candidates
        candidate_paths = []
        for cf in valid_candidates:
            ext = _get_ext(cf.filename)
            path = os.path.join(batch_dir, f'cand_{uuid.uuid4().hex}{ext}')
            cf.save(path)
            candidate_paths.append(path)
        
        # Run batch comparison
        results = orchestrator.batch_compare(ref_path, candidate_paths)
        
        return jsonify(success=True, count=len(results), results=results)
    
    except Exception as e:
        return jsonify(success=False, error=str(e)), 500
    
    finally:
        # Clean up all temp files
        if os.path.exists(batch_dir):
            import shutil
            shutil.rmtree(batch_dir, ignore_errors=True)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_app.py::TestBatchCompare -v`

Expected: PASS

- [ ] **Step 5: Run all tests to check nothing broken**

Run: `python -m pytest -v`

Expected: 29+ tests pass (4 new + 25 existing)

- [ ] **Step 6: Commit**

```bash
git add app.py tests/test_app.py
git commit -m "feat: add /compare-batch API endpoint"
```

---

### Task 3: Upload page with two dropzones

**Files:**
- Modify: `templates/index.html`
- Modify: `static/js/main.js`
- Modify: `static/css/style.css`

- [ ] **Step 1: Update index.html with two dropzones**

Replace the upload section in `templates/index.html`:

The page should have:
1. Reference dropzone (single image, with "Reference Image" label)
2. Candidates dropzone (multiple images, with "Candidate Images" label, shows count)
3. "Compare All" button
4. Preview of reference image + file list of candidates

```html
<div class="upload-section">
  <div class="dropzone-row">
    <!-- Reference dropzone -->
    <div class="dropzone-wrapper">
      <h3>Reference Image</h3>
      <p class="dropzone-hint">The image to match against</p>
      <div class="dropzone" id="ref-dropzone">
        <div class="dropzone-content">
          <span class="dropzone-icon">📷</span>
          <p>Drag & drop reference image here</p>
          <p class="small">or click to browse</p>
          <input type="file" id="ref-input" accept="image/*" hidden>
        </div>
        <div class="preview" id="ref-preview" hidden>
          <img id="ref-img" alt="Reference preview">
          <button class="remove-btn" id="ref-remove">✕</button>
        </div>
      </div>
    </div>
    
    <!-- Candidates dropzone -->
    <div class="dropzone-wrapper">
      <h3>Candidate Images</h3>
      <p class="dropzone-hint">Images to compare against reference</p>
      <div class="dropzone" id="cand-dropzone">
        <div class="dropzone-content">
          <span class="dropzone-icon">📁</span>
          <p>Drag & drop candidate images here</p>
          <p class="small">or click to browse (select multiple)</p>
          <input type="file" id="cand-input" accept="image/*" multiple hidden>
        </div>
        <div class="file-list" id="cand-list" hidden>
          <p class="file-count"><span id="cand-count">0</span> images selected</p>
          <button class="remove-btn" id="cand-clear">Clear all</button>
        </div>
      </div>
    </div>
  </div>
  
  <button class="compare-btn" id="batch-compare-btn" disabled>
    🚀 Compare All
  </button>
  <div id="loading" hidden>
    <div class="spinner"></div>
    <p id="loading-text">Comparing images...</p>
  </div>
</div>
```

Remove old single-upload dropzone and old compare button.

- [ ] **Step 2: Update main.js with batch upload logic**

Replace the JavaScript in `static/js/main.js`:

```javascript
// Reference dropzone
const refDropzone = document.getElementById('ref-dropzone');
const refInput = document.getElementById('ref-input');
const refPreview = document.getElementById('ref-preview');
const refImg = document.getElementById('ref-img');
const refRemove = document.getElementById('ref-remove');

let refFile = null;
let candFiles = [];

// Reference: click to browse
refDropzone.addEventListener('click', () => refInput.click());
refInput.addEventListener('change', (e) => {
  if (e.target.files[0]) handleRefFile(e.target.files[0]);
});

// Reference: drag & drop
refDropzone.addEventListener('dragover', (e) => { e.preventDefault(); refDropzone.classList.add('dragover'); });
refDropzone.addEventListener('dragleave', () => refDropzone.classList.remove('dragover'));
refDropzone.addEventListener('drop', (e) => {
  e.preventDefault();
  refDropzone.classList.remove('dragover');
  if (e.dataTransfer.files[0]) handleRefFile(e.dataTransfer.files[0]);
});

function handleRefFile(file) {
  refFile = file;
  const reader = new FileReader();
  reader.onload = (e) => {
    refImg.src = e.target.result;
    refPreview.hidden = false;
    refDropzone.querySelector('.dropzone-content').hidden = true;
  };
  reader.readAsDataURL(file);
  updateCompareBtn();
}

refRemove.addEventListener('click', (e) => {
  e.stopPropagation();
  refFile = null;
  refPreview.hidden = true;
  refDropzone.querySelector('.dropzone-content').hidden = false;
  refInput.value = '';
  updateCompareBtn();
});

// Candidates dropzone
const candDropzone = document.getElementById('cand-dropzone');
const candInput = document.getElementById('cand-input');
const candList = document.getElementById('cand-list');
const candCount = document.getElementById('cand-count');
const candClear = document.getElementById('cand-clear');

candDropzone.addEventListener('click', () => candInput.click());
candInput.addEventListener('change', (e) => {
  if (e.target.files.length) handleCandFiles(e.target.files);
});

candDropzone.addEventListener('dragover', (e) => { e.preventDefault(); candDropzone.classList.add('dragover'); });
candDropzone.addEventListener('dragleave', () => candDropzone.classList.remove('dragover'));
candDropzone.addEventListener('drop', (e) => {
  e.preventDefault();
  candDropzone.classList.remove('dragover');
  if (e.dataTransfer.files.length) handleCandFiles(e.dataTransfer.files);
});

function handleCandFiles(files) {
  candFiles = [...candFiles, ...Array.from(files)];
  candCount.textContent = candFiles.length;
  candList.hidden = false;
  updateCompareBtn();
}

candClear.addEventListener('click', (e) => {
  e.stopPropagation();
  candFiles = [];
  candCount.textContent = '0';
  candList.hidden = true;
  candInput.value = '';
  updateCompareBtn();
});

function updateCompareBtn() {
  document.getElementById('batch-compare-btn').disabled = !(refFile && candFiles.length > 0);
}

// Submit batch comparison
document.getElementById('batch-compare-btn').addEventListener('click', async () => {
  const formData = new FormData();
  formData.append('reference', refFile);
  candFiles.forEach(f => formData.append('candidates', f));
  
  document.getElementById('loading').hidden = false;
  document.getElementById('batch-compare-btn').disabled = true;
  
  try {
    const resp = await fetch('/compare-batch', { method: 'POST', body: formData });
    const data = await resp.json();
    
    if (data.success) {
      // Store results and redirect
      sessionStorage.setItem('batchResults', JSON.stringify(data.results));
      window.location.href = '/batch-results';
    } else {
      alert('Error: ' + data.error);
    }
  } catch (err) {
    alert('Error: ' + err.message);
  } finally {
    document.getElementById('loading').hidden = true;
  }
});

// Theme toggle
document.getElementById('theme-toggle')?.addEventListener('click', () => {
  document.body.classList.toggle('dark');
  localStorage.setItem('theme', document.body.classList.contains('dark') ? 'dark' : 'light');
});

// Load saved theme
if (localStorage.getItem('theme') === 'dark') {
  document.body.classList.add('dark');
}
```

- [ ] **Step 3: Update styles**

Add to `static/css/style.css`:

```css
/* Two-dropzone layout */
.dropzone-row {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
}

.dropzone-wrapper {
  flex: 1;
}

.dropzone-wrapper h3 {
  margin: 0 0 5px;
  font-size: 1.1em;
}

.dropzone-hint {
  font-size: 0.85em;
  opacity: 0.7;
  margin: 0 0 10px;
}

/* File list in candidate dropzone */
.file-list {
  text-align: center;
  padding: 20px;
}

.file-count {
  font-weight: 600;
  margin: 0 0 10px;
}

/* Keep existing dropzone styles, add adjustments */
.dropzone .preview {
  position: relative;
}

.dropzone .preview img {
  max-height: 180px;
  border-radius: 8px;
}

.remove-btn {
  position: absolute;
  top: 5px;
  right: 5px;
  background: rgba(0,0,0,0.6);
  color: white;
  border: none;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  cursor: pointer;
  font-size: 12px;
}

/* Compare all button */
.compare-btn {
  display: block;
  width: 100%;
  padding: 15px;
  font-size: 1.2em;
  border: none;
  border-radius: 8px;
  background: var(--primary);
  color: white;
  cursor: pointer;
  transition: opacity 0.3s;
}

.compare-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
```

- [ ] **Step 4: Run tests to verify**

Run: `python -m pytest -v`

Expected: All tests pass (frontend changes don't affect tests)

- [ ] **Step 5: Commit**

```bash
git add templates/index.html static/js/main.js static/css/style.css
git commit -m "feat: update upload page with reference + candidates dropzones"
```

---

### Task 4: Batch results page

**Files:**
- Create: `templates/batch_results.html`
- Modify: `app.py` (add `/batch-results` route)
- Modify: `static/css/style.css` (add results table styles)

- [ ] **Step 1: Add route to app.py**

```python
@app.route('/batch-results')
def batch_results():
    """Render batch results page."""
    return render_template('batch_results.html')
```

- [ ] **Step 2: Write test for results page**

Add to `tests/test_app.py`:

```python
def test_batch_results_page(app):
    """Test batch results page loads."""
    with app.test_client() as client:
        resp = client.get('/batch-results')
        assert resp.status_code == 200
        assert b'Batch Results' in resp.data or b'Rank' in resp.data
```

- [ ] **Step 3: Create batch_results.html**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Batch Results - Image Accuracy Finder</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
  <style>
    .results-table { width: 100%; border-collapse: collapse; }
    .results-table th, .results-table td { padding: 12px; text-align: left; border-bottom: 1px solid var(--border); }
    .results-table th { cursor: pointer; user-select: none; }
    .results-table tr:hover { background: var(--hover); }
    .rank-badge { display: inline-block; width: 28px; height: 28px; line-height: 28px; text-align: center; border-radius: 50%; font-weight: 700; font-size: 0.85em; }
    .rank-1 { background: gold; color: #333; }
    .rank-2 { background: silver; color: #333; }
    .rank-3 { background: #cd7f32; color: white; }
    .score-bar { height: 8px; border-radius: 4px; background: var(--border); overflow: hidden; min-width: 100px; }
    .score-fill { height: 100%; border-radius: 4px; transition: width 0.6s ease; }
    .thumbnail { width: 48px; height: 48px; object-fit: cover; border-radius: 4px; }
    .breakdown { display: none; }
    .breakdown.visible { display: table-row; }
    .breakdown td { padding: 8px 12px 8px 60px; }
    .breakdown-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
    .breakdown-item { text-align: center; }
    .breakdown-item .label { font-size: 0.8em; opacity: 0.7; }
    .breakdown-item .value { font-size: 1.1em; font-weight: 600; }
    .loading-results { text-align: center; padding: 60px; }
    .pagination { display: flex; justify-content: center; gap: 8px; margin-top: 20px; }
    .pagination button { padding: 8px 16px; border: 1px solid var(--border); background: var(--bg); border-radius: 6px; cursor: pointer; }
    .pagination button.active { background: var(--primary); color: white; border-color: var(--primary); }
    .pagination button:disabled { opacity: 0.4; cursor: not-allowed; }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>📊 Batch Results</h1>
      <div class="header-actions">
        <a href="/" class="btn">⬅ Back</a>
        <button id="theme-toggle">🌓</button>
      </div>
    </header>
    
    <div id="results-summary" hidden>
      <p>Sorted by similarity — <span id="result-count"></span> images compared</p>
    </div>
    
    <div id="loading-results" class="loading-results">
      <div class="spinner"></div>
      <p>Loading results...</p>
    </div>
    
    <div id="no-results" hidden>
      <p>No results found. <a href="/">Upload images</a> to compare.</p>
    </div>
    
    <div id="results-content" hidden>
      <table class="results-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Image</th>
            <th>Filename</th>
            <th>Similarity</th>
            <th></th>
          </tr>
        </thead>
        <tbody id="results-body"></tbody>
      </table>
      <div class="pagination" id="pagination"></div>
    </div>
  </div>
  
  <script>
    const PER_PAGE = 20;
    let results = [];
    let currentPage = 1;
    
    function getScoreColor(score) {
      if (score >= 80) return '#22c55e';
      if (score >= 60) return '#eab308';
      if (score >= 40) return '#f97316';
      return '#ef4444';
    }
    
    function renderPage(page) {
      currentPage = page;
      const tbody = document.getElementById('results-body');
      tbody.innerHTML = '';
      const start = (page - 1) * PER_PAGE;
      const end = Math.min(start + PER_PAGE, results.length);
      
      for (let i = start; i < end; i++) {
        const r = results[i];
        const rank = i + 1;
        const rankClass = rank <= 3 ? `rank-${rank}` : '';
        const color = getScoreColor(r.overall);
        
        const row = document.createElement('tr');
        row.innerHTML = `
          <td><span class="rank-badge ${rankClass}">${rank}</span></td>
          <td><div class="thumbnail" style="background:#eee;display:flex;align-items:center;justify-content:center;color:#999;font-size:20px;">🖼</div></td>
          <td>${r.filename}</td>
          <td>
            <div style="display:flex;align-items:center;gap:12px;">
              <div class="score-bar">
                <div class="score-fill" style="width:${r.overall}%;background:${color};"></div>
              </div>
              <strong>${r.overall.toFixed(1)}%</strong>
            </div>
          </td>
          <td><button onclick="toggleBreakdown(${i})" style="background:none;border:1px solid var(--border);border-radius:4px;padding:4px 8px;cursor:pointer;">Details</button></td>
        `;
        row.dataset.index = i;
        tbody.appendChild(row);
        
        // Breakdown row
        const br = document.createElement('tr');
        br.className = 'breakdown';
        br.id = `breakdown-${i}`;
        br.innerHTML = `
          <td colspan="5">
            <div class="breakdown-grid">
              <div class="breakdown-item">
                <div class="label">SSIM</div>
                <div class="value" style="color:${getScoreColor(r.ssim)}">${r.ssim.toFixed(1)}%</div>
              </div>
              <div class="breakdown-item">
                <div class="label">ORB</div>
                <div class="value" style="color:${getScoreColor(r.orb)}">${r.orb.toFixed(1)}%</div>
              </div>
              <div class="breakdown-item">
                <div class="label">Histogram</div>
                <div class="value" style="color:${getScoreColor(r.histogram)}">${r.histogram.toFixed(1)}%</div>
              </div>
              <div class="breakdown-item">
                <div class="label">pHash</div>
                <div class="value" style="color:${getScoreColor(r.phash)}">${r.phash.toFixed(1)}%</div>
              </div>
            </div>
          </td>
        `;
        tbody.appendChild(br);
      }
      
      renderPagination();
    }
    
    function renderPagination() {
      const pages = Math.ceil(results.length / PER_PAGE);
      const container = document.getElementById('pagination');
      container.innerHTML = '';
      
      const prev = document.createElement('button');
      prev.textContent = '◀';
      prev.disabled = currentPage === 1;
      prev.onclick = () => renderPage(currentPage - 1);
      container.appendChild(prev);
      
      for (let i = 1; i <= pages; i++) {
        const btn = document.createElement('button');
        btn.textContent = i;
        btn.className = i === currentPage ? 'active' : '';
        btn.onclick = () => renderPage(i);
        container.appendChild(btn);
      }
      
      const next = document.createElement('button');
      next.textContent = '▶';
      next.disabled = currentPage === pages;
      next.onclick = () => renderPage(currentPage + 1);
      container.appendChild(next);
    }
    
    function toggleBreakdown(index) {
      const el = document.getElementById(`breakdown-${index}`);
      el.classList.toggle('visible');
    }
    
    // Load results
    document.addEventListener('DOMContentLoaded', () => {
      const stored = sessionStorage.getItem('batchResults');
      if (stored) {
        results = JSON.parse(stored);
        document.getElementById('result-count').textContent = results.length;
        document.getElementById('results-summary').hidden = false;
        document.getElementById('loading-results').hidden = true;
        document.getElementById('results-content').hidden = false;
        renderPage(1);
      } else {
        document.getElementById('loading-results').hidden = true;
        document.getElementById('no-results').hidden = false;
      }
    });
    
    // Theme toggle
    document.getElementById('theme-toggle').addEventListener('click', () => {
      document.body.classList.toggle('dark');
      localStorage.setItem('theme', document.body.classList.contains('dark') ? 'dark' : 'light');
    });
    if (localStorage.getItem('theme') === 'dark') document.body.classList.add('dark');
  </script>
</body>
</html>
```

- [ ] **Step 4: Run tests to verify**

Run: `python -m pytest -v`

Expected: All tests pass

- [ ] **Step 5: Commit**

```bash
git add templates/batch_results.html app.py tests/test_app.py static/css/style.css
git commit -m "feat: add batch results page with ranked table"
```

---

### Task 5: Final verification

- [ ] **Step 1: Run full test suite**

Run: `python -m pytest -v`

Expected: All 29+ tests pass

- [ ] **Step 2: Push to GitHub**

```bash
git push origin master
```

- [ ] **Step 3: Report summary**
