// === DOM References ===
const form = document.getElementById('compareForm');
const btnCompare = document.getElementById('btnCompare');
const zoneA = document.getElementById('zoneA');
const zoneB = document.getElementById('zoneB');
const inputA = document.getElementById('imageA');
const inputB = document.getElementById('imageB');
const loadingOverlay = document.getElementById('loadingOverlay');
const themeToggle = document.getElementById('themeToggle');

// === Theme Toggle ===
let isDark = true;
themeToggle.addEventListener('click', () => {
    isDark = !isDark;
    document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
    document.body.classList.toggle('light-theme', !isDark);
    themeToggle.textContent = isDark ? '🌙' : '☀️';
});

// === Drag & Drop + File Selection ===
function setupUploadZone(zone, input) {
    // Click to upload
    zone.addEventListener('click', () => input.click());

    input.addEventListener('change', () => {
        if (input.files.length > 0) {
            previewImage(zone, input.files[0]);
        }
        updateButtonState();
    });

    // Drag & drop
    zone.addEventListener('dragover', (e) => {
        e.preventDefault();
        zone.classList.add('dragover');
    });

    zone.addEventListener('dragleave', () => {
        zone.classList.remove('dragover');
    });

    zone.addEventListener('drop', (e) => {
        e.preventDefault();
        zone.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            const file = e.dataTransfer.files[0];
            const validTypes = ['image/png', 'image/jpeg', 'image/webp'];
            if (!validTypes.includes(file.type)) {
                alert('Please upload a PNG, JPG, or WEBP image.');
                return;
            }
            if (file.size > 16 * 1024 * 1024) {
                alert('File is too large. Maximum is 16MB.');
                return;
            }
            input.files = e.dataTransfer.files;
            previewImage(zone, file);
            updateButtonState();
        }
    });
}

function previewImage(zone, file) {
    const reader = new FileReader();
    reader.onload = (e) => {
        zone.classList.add('has-image');
        zone.innerHTML = `
            <img src="${e.target.result}" class="upload-preview" alt="Preview">
            <p style="color: var(--text-secondary); font-size: 0.9rem;">${file.name}</p>
        `;
    };
    reader.readAsDataURL(file);
}

function updateButtonState() {
    const hasBoth = inputA.files.length > 0 && inputB.files.length > 0;
    btnCompare.classList.toggle('active', hasBoth);
    btnCompare.disabled = !hasBoth;
}

// Initialize upload zones
setupUploadZone(zoneA, inputA);
setupUploadZone(zoneB, inputB);

// === Form Submission ===
form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const formData = new FormData();
    formData.append('image_a', inputA.files[0]);
    formData.append('image_b', inputB.files[0]);

    loadingOverlay.classList.add('active');

    try {
        const response = await fetch('/compare', {
            method: 'POST',
            body: formData,
        });

        const data = await response.json();

        if (data.success) {
            window.location.href = `/results/${data.id}`;
        } else {
            alert('Error: ' + (data.error || 'Unknown error occurred'));
            loadingOverlay.classList.remove('active');
        }
    } catch (err) {
        alert('Network error. Please try again.');
        loadingOverlay.classList.remove('active');
    }
});
