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

const MAX_SIZE = 500 * 1024 * 1024; // 500MB

function validateFile(file) {
  // Accept any file type that starts with 'image/' or has no type (unknown but let server decide)
  if (file.type && !file.type.startsWith('image/')) {
    alert(`"${file.name}" is not a supported image type (${file.type}). Please use PNG, JPG, or WEBP.`);
    return false;
  }
  if (file.size > MAX_SIZE) {
    alert(`"${file.name}" is too large (max 500MB).`);
    return false;
  }
  return true;
}

function handleRefFile(file) {
  if (!validateFile(file)) return;
  refFile = file;
  const reader = new FileReader();
  reader.onload = (e) => {
    refImg.src = e.target.result;
    refPreview.hidden = false;
    refDropzone.querySelector('.dropzone-content').hidden = true;
    refDropzone.classList.add('has-image');
  };
  reader.readAsDataURL(file);
  updateCompareBtn();
}

refRemove.addEventListener('click', (e) => {
  e.stopPropagation();
  refFile = null;
  refPreview.hidden = true;
  refDropzone.querySelector('.dropzone-content').hidden = false;
  refDropzone.classList.remove('has-image');
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
  const valid = Array.from(files).filter(f => validateFile(f));
  candFiles = [...candFiles, ...valid];
  candCount.textContent = candFiles.length;
  candList.hidden = candFiles.length === 0;
  if (candFiles.length > 0) candDropzone.classList.add('has-image');
  updateCompareBtn();
}

candClear.addEventListener('click', (e) => {
  e.stopPropagation();
  candFiles = [];
  candCount.textContent = '0';
  candList.hidden = true;
  candDropzone.classList.remove('has-image');
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
    if (!resp.ok) {
      const text = await resp.text();
      throw new Error(`Server error (${resp.status}): ${text.slice(0, 200)}`);
    }
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
document.getElementById('themeToggle')?.addEventListener('click', () => {
  const isLight = document.body.classList.toggle('light-theme');
  document.getElementById('themeToggle').textContent = isLight ? '☀️' : '🌙';
  localStorage.setItem('theme', isLight ? 'light' : 'dark');
});

// Load saved theme
if (localStorage.getItem('theme') === 'light') {
  document.body.classList.add('light-theme');
  document.getElementById('themeToggle').textContent = '☀️';
}