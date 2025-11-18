// SnackSwap Comics - Frontend Application
const API_BASE = 'http://localhost:8000/api';

// State
let currentPhotoId = null;
let currentScriptId = null;
let selectedFile = null;

// DOM Elements
const uploadBox = document.getElementById('uploadBox');
const fileInput = document.getElementById('fileInput');
const preview = document.getElementById('preview');
const ageInput = document.getElementById('ageInput');
const generateBtn = document.getElementById('generateBtn');
const progressSection = document.getElementById('progressSection');
const resultsSection = document.getElementById('resultsSection');
const errorSection = document.getElementById('errorSection');

// Upload Box - Click and Drag & Drop
uploadBox.addEventListener('click', () => fileInput.click());

uploadBox.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadBox.classList.add('dragover');
});

uploadBox.addEventListener('dragleave', () => {
    uploadBox.classList.remove('dragover');
});

uploadBox.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadBox.classList.remove('dragover');

    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFile(e.target.files[0]);
    }
});

function handleFile(file) {
    if (!file.type.startsWith('image/')) {
        showError('Please select an image file');
        return;
    }

    selectedFile = file;

    // Show preview
    const reader = new FileReader();
    reader.onload = (e) => {
        preview.src = e.target.result;
        preview.classList.remove('hidden');
    };
    reader.readAsDataURL(file);

    // Enable generate button
    generateBtn.disabled = false;
}

// Generate Comic
generateBtn.addEventListener('click', async () => {
    if (!selectedFile) {
        showError('Please select an image first');
        return;
    }

    const age = parseInt(ageInput.value);
    if (!age || age < 3 || age > 12) {
        showError('Please enter a valid age (3-12)');
        return;
    }

    hideError();
    hideResults();
    showProgress();
    generateBtn.disabled = true;

    try {
        // Step 1: Upload image
        setStepActive('step1');
        const photoData = await uploadImage(selectedFile);
        currentPhotoId = photoData.photo_id;
        setStepComplete('step1');

        // Step 2: Detect items
        setStepActive('step2');
        const detectionData = await detectItems(currentPhotoId);
        setStepComplete('step2');

        // Step 3: Score and retrieve
        setStepActive('step3');
        const scoreData = await scoreAndRetrieve(detectionData.items, age);
        setStepComplete('step3');

        // Step 4: Compose script
        setStepActive('step4');
        const scriptData = await composeScript(currentPhotoId, scoreData, age);
        currentScriptId = scriptData.script_id;
        setStepComplete('step4');

        // Step 5: Render comic
        setStepActive('step5');
        const renderData = await renderComic(currentScriptId);
        setStepComplete('step5');

        // Display results
        displayResults(detectionData, scoreData, scriptData, renderData);

    } catch (error) {
        showError(error.message || 'Something went wrong. Please try again.');
        console.error(error);
    } finally {
        hideProgress();
        generateBtn.disabled = false;
    }
});

// API Functions
async function uploadImage(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE}/capture/intake`, {
        method: 'POST',
        body: formData,
    });

    if (!response.ok) {
        throw new Error('Failed to upload image');
    }

    return await response.json();
}

async function detectItems(photoId) {
    const response = await fetch(`${API_BASE}/vision/detect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ photo_id: photoId }),
    });

    if (!response.ok) {
        throw new Error('Failed to detect items');
    }

    return await response.json();
}

async function scoreAndRetrieve(items, age) {
    const response = await fetch(`${API_BASE}/score/retrieve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            items: items,
            age: age,
            allergies: [],
        }),
    });

    if (!response.ok) {
        throw new Error('Failed to score items');
    }

    return await response.json();
}

async function composeScript(photoId, scoreData, age) {
    const response = await fetch(`${API_BASE}/script/compose`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            photo_id: photoId,
            scored_items: scoreData.scored_items,
            facts: scoreData.facts,
            swaps: scoreData.swaps,
            age: age,
        }),
    });

    if (!response.ok) {
        throw new Error('Failed to compose script');
    }

    return await response.json();
}

async function renderComic(scriptId) {
    const response = await fetch(`${API_BASE}/render/comic`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ script_id: scriptId }),
    });

    if (!response.ok) {
        throw new Error('Failed to render comic');
    }

    return await response.json();
}

// UI Helper Functions
function setStepActive(stepId) {
    const step = document.getElementById(stepId);
    step.classList.add('active');
}

function setStepComplete(stepId) {
    const step = document.getElementById(stepId);
    step.classList.remove('active');
    step.classList.add('complete');
}

function showProgress() {
    progressSection.classList.remove('hidden');
    // Reset all steps
    for (let i = 1; i <= 5; i++) {
        const step = document.getElementById(`step${i}`);
        step.classList.remove('active', 'complete');
    }
}

function hideProgress() {
    progressSection.classList.add('hidden');
}

function showError(message) {
    errorSection.textContent = `❌ Error: ${message}`;
    errorSection.classList.remove('hidden');
}

function hideError() {
    errorSection.classList.add('hidden');
}

function showResults() {
    resultsSection.classList.remove('hidden');
}

function hideResults() {
    resultsSection.classList.add('hidden');
}

function displayResults(detectionData, scoreData, scriptData, renderData) {
    // Detection info
    const detectionInfo = document.getElementById('detectionInfo');
    const item = detectionData.items[0];
    detectionInfo.innerHTML = `
        <h4>${item.name}</h4>
        <p><strong>Category:</strong> ${item.category}</p>
        <p><strong>Confidence:</strong> ${(item.confidence * 100).toFixed(1)}%</p>
    `;

    // Risk score
    const riskScore = document.getElementById('riskScore');
    const scoredItem = scoreData.scored_items[0];
    const score = scoredItem.dental_risk_score;
    let riskClass = 'risk-low';
    let riskLabel = 'Low Risk';

    if (score > 70) {
        riskClass = 'risk-high';
        riskLabel = 'High Risk';
    } else if (score > 40) {
        riskClass = 'risk-medium';
        riskLabel = 'Medium Risk';
    }

    riskScore.innerHTML = `
        <div class="${riskClass}">
            Dental Risk Score: ${score.toFixed(1)}/100
            <div style="font-size: 0.6em; margin-top: 10px;">${riskLabel}</div>
        </div>
    `;

    // Facts
    const factsInfo = document.getElementById('factsInfo');
    factsInfo.innerHTML = scoreData.facts.map((fact, i) => `
        <div class="fact">
            <strong>Fact ${i + 1}:</strong> ${fact.text}
        </div>
    `).join('');

    // Comic image (use square format by default)
    const comicImage = document.getElementById('comicImage');
    const baseUrl = 'http://localhost:8000';
    comicImage.src = `${baseUrl}${renderData.comic_square_uri}?t=${Date.now()}`;

    // Download buttons
    setupDownloadButton('downloadSquare', renderData.comic_square_uri, 'snackswap-comic-square.png');
    setupDownloadButton('downloadPortrait', renderData.comic_portrait_uri, 'snackswap-comic-portrait.png');
    setupDownloadButton('downloadReel', renderData.reel_cover_uri, 'snackswap-comic-reel.png');

    showResults();

    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

function setupDownloadButton(buttonId, uri, filename) {
    const button = document.getElementById(buttonId);
    button.onclick = async () => {
        try {
            const response = await fetch(`http://localhost:8000${uri}`);
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (error) {
            showError('Failed to download file');
        }
    };
}
