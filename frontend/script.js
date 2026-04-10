const API_BASE_URL = 'http://localhost:5000/api';

let currentText = '';

// Tab switching
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const tab = btn.dataset.tab;
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById(`${tab}-tab`).classList.add('active');
    });
});

// Image upload
const imageUploadArea = document.getElementById('imageUploadArea');
const imageInput = document.getElementById('imageInput');
const imagePreview = document.getElementById('imagePreview');

imageUploadArea.addEventListener('click', () => imageInput.click());
imageUploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    imageUploadArea.style.borderColor = '#667eea';
});
imageUploadArea.addEventListener('dragleave', () => {
    imageUploadArea.style.borderColor = '#ccc';
});
imageUploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
        handleImageFile(file);
    }
});

imageInput.addEventListener('change', (e) => {
    if (e.target.files[0]) {
        handleImageFile(e.target.files[0]);
    }
});

function handleImageFile(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
        imagePreview.innerHTML = `<img src="${e.target.result}" alt="Preview">`;
    };
    reader.readAsDataURL(file);
    window.currentImageFile = file;
}

// Video upload
const videoUploadArea = document.getElementById('videoUploadArea');
const videoInput = document.getElementById('videoInput');
const videoPreview = document.getElementById('videoPreview');

videoUploadArea.addEventListener('click', () => videoInput.click());
videoInput.addEventListener('change', (e) => {
    if (e.target.files[0]) {
        const file = e.target.files[0];
        const url = URL.createObjectURL(file);
        videoPreview.innerHTML = `<video controls><source src="${url}"></video>`;
        window.currentVideoFile = file;
    }
});

// Process Image
document.getElementById('processImageBtn').addEventListener('click', async () => {
    if (!window.currentImageFile) {
        alert('Please select an image first');
        return;
    }
    
    showLoading();
    
    const formData = new FormData();
    formData.append('image', window.currentImageFile);
    
    try {
        const response = await fetch(`${API_BASE_URL}/ocr/image`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayResults(data);
            currentText = data.text;
            enableButtons();
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        alert('Error processing image: ' + error.message);
    } finally {
        hideLoading();
    }
});

// Process Video
document.getElementById('processVideoBtn').addEventListener('click', async () => {
    if (!window.currentVideoFile) {
        alert('Please select a video first');
        return;
    }
    
    showLoading();
    
    const formData = new FormData();
    formData.append('video', window.currentVideoFile);
    
    try {
        const response = await fetch(`${API_BASE_URL}/ocr/video`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayResults(data);
            currentText = data.text;
            enableButtons();
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        alert('Error processing video: ' + error.message);
    } finally {
        hideLoading();
    }
});

// RAG Query
document.getElementById('askBtn').addEventListener('click', async () => {
    const question = document.getElementById('questionInput').value.trim();
    
    if (!question) {
        alert('Please enter a question');
        return;
    }
    
    if (!currentText) {
        alert('Please extract text from an image or video first');
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch(`${API_BASE_URL}/rag/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ question })
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayAnswer(data.answer);
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        alert('Error querying RAG: ' + error.message);
    } finally {
        hideLoading();
    }
});

// Copy Text
document.getElementById('copyTextBtn').addEventListener('click', () => {
    navigator.clipboard.writeText(currentText);
    alert('Text copied to clipboard!');
});

// Download Text
document.getElementById('downloadTextBtn').addEventListener('click', () => {
    const blob = new Blob([currentText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ocr_text_${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
});

function displayResults(data) {
    const ocrDiv = document.getElementById('ocrText');
    ocrDiv.innerHTML = `<pre>${escapeHtml(data.text)}</pre>`;
    
    document.getElementById('stats').style.display = 'flex';
    document.getElementById('charCount').textContent = data.char_count;
    document.getElementById('wordCount').textContent = data.word_count;
    
    if (data.summary) {
        document.getElementById('summaryBox').style.display = 'block';
        document.getElementById('summary').innerHTML = `<p>${escapeHtml(data.summary)}</p>`;
    }
}

function displayAnswer(answer) {
    const answerBox = document.getElementById('answerBox');
    answerBox.innerHTML = `
        <div class="answer-content">
            <i class="fas fa-lightbulb" style="color: #667eea;"></i>
            <p>${escapeHtml(answer)}</p>
        </div>
    `;
}

function enableButtons() {
    document.getElementById('copyTextBtn').disabled = false;
    document.getElementById('downloadTextBtn').disabled = false;
}

function showLoading() {
    document.getElementById('loadingOverlay').style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loadingOverlay').style.display = 'none';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Load summary on demand
async function loadSummary() {
    if (!currentText) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/rag/summary`);
        const data = await response.json();
        
        if (data.success && data.summary) {
            document.getElementById('summaryBox').style.display = 'block';
            document.getElementById('summary').innerHTML = `<p>${escapeHtml(data.summary)}</p>`;
        }
    } catch (error) {
        console.error('Error loading summary:', error);
    }
}