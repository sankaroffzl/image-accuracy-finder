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
document.getElementById('themeToggle')?.addEventListener('click', () => {
  document.body.classList.toggle('dark');
  localStorage.setItem('theme', document.body.classList.contains('dark') ? 'dark' : 'light');
});

// Load saved theme
if (localStorage.getItem('theme') === 'dark') {
  document.body.classList.add('dark');
}