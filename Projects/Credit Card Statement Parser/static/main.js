// Global variables
let selectedFiles = [];
const MAX_FILES = 5;
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

// DOM Elements
const uploadSection = document.getElementById('uploadSection');
const fileInput = document.getElementById('fileInput');
const fileList = document.getElementById('fileList');
const parseBtn = document.getElementById('parseBtn');
const clearBtn = document.getElementById('clearBtn');
const loading = document.getElementById('loading');
const results = document.getElementById('results');
const resultsContainer = document.getElementById('resultsContainer');
const summary = document.getElementById('summary');
const downloadSection = document.getElementById('downloadSection');
const downloadJson = document.getElementById('downloadJson');
const downloadCsv = document.getElementById('downloadCsv');

// Event Listeners
uploadSection.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', handleFileSelect);
parseBtn.addEventListener('click', parseStatements);
clearBtn.addEventListener('click', clearAll);
downloadJson.addEventListener('click', () => downloadFile('json'));
downloadCsv.addEventListener('click', () => downloadFile('csv'));

// Drag and Drop
uploadSection.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadSection.classList.add('dragover');
});

uploadSection.addEventListener('dragleave', () => {
    uploadSection.classList.remove('dragover');
});

uploadSection.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadSection.classList.remove('dragover');
    
    const files = Array.from(e.dataTransfer.files);
    addFiles(files);
});

// Handle File Selection
function handleFileSelect(event) {
    const files = Array.from(event.target.files);
    addFiles(files);
}

// Add Files
function addFiles(files) {
    // Filter PDF files only
    const pdfFiles = files.filter(file => file.type === 'application/pdf');
    
    if (pdfFiles.length === 0) {
        alert('Please select PDF files only.');
        return;
    }
    
    // Check total files count
    if (selectedFiles.length + pdfFiles.length > MAX_FILES) {
        alert(`You can only upload up to ${MAX_FILES} files.`);
        return;
    }
    
    // Check file sizes
    const oversizedFiles = pdfFiles.filter(file => file.size > MAX_FILE_SIZE);
    if (oversizedFiles.length > 0) {
        alert(`Some files exceed 10MB limit: ${oversizedFiles.map(f => f.name).join(', ')}`);
        return;
    }
    
    // Add files
    selectedFiles = [...selectedFiles, ...pdfFiles];
    updateFileList();
    updateParseButton();
}

// Update File List Display
function updateFileList() {
    if (selectedFiles.length === 0) {
        fileList.style.display = 'none';
        return;
    }
    
    fileList.style.display = 'block';
    fileList.innerHTML = selectedFiles.map((file, index) => `
        <div class="file-item">
            <span class="file-name">📄 ${file.name} (${formatFileSize(file.size)})</span>
            <button class="file-remove" onclick="removeFile(${index})">Remove</button>
        </div>
    `).join('');
}

// Remove File
function removeFile(index) {
    selectedFiles.splice(index, 1);
    updateFileList();
    updateParseButton();
}

// Update Parse Button State
function updateParseButton() {
    parseBtn.disabled = selectedFiles.length === 0;
}

// Clear All
function clearAll() {
    selectedFiles = [];
    fileInput.value = '';
    updateFileList();
    updateParseButton();
    results.style.display = 'none';
    downloadSection.style.display = 'none';
}

// Format File Size
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
}

// Parse Statements
async function parseStatements() {
    if (selectedFiles.length === 0) return;
    
    // Show loading
    loading.style.display = 'block';
    results.style.display = 'none';
    downloadSection.style.display = 'none';
    parseBtn.disabled = true;
    
    // Prepare FormData
    const formData = new FormData();
    selectedFiles.forEach(file => {
        formData.append('files[]', file);
    });
    
    try {
        // Send request to backend
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Hide loading
        loading.style.display = 'none';
        
        // Display results
        displayResults(data);
        
    } catch (error) {
        loading.style.display = 'none';
        alert(`Error: ${error.message}`);
        parseBtn.disabled = false;
    }
}

// Display Results
function displayResults(data) {
    results.style.display = 'block';
    
    // Display summary
    const successCount = data.results.filter(r => r.status === 'success').length;
    const partialCount = data.results.filter(r => r.status === 'partial').length;
    const errorCount = data.results.filter(r => r.status === 'error').length;
    
    summary.innerHTML = `
        <h3>Parsing Summary</h3>
        <div class="summary-stats">
            <div class="stat">
                <div class="stat-value">${data.results.length}</div>
                <div class="stat-label">Total Files</div>
            </div>
            <div class="stat">
                <div class="stat-value">${successCount}</div>
                <div class="stat-label">Successful</div>
            </div>
            <div class="stat">
                <div class="stat-value">${partialCount}</div>
                <div class="stat-label">Partial</div>
            </div>
            <div class="stat">
                <div class="stat-value">${errorCount}</div>
                <div class="stat-label">Errors</div>
            </div>
        </div>
    `;
    
    // Display individual results
    resultsContainer.innerHTML = data.results.map(result => `
        <div class="result-card ${result.status}">
            <div class="bank-name">
                ${result.bank.toUpperCase()} - ${result.filename}
                <span class="status-badge ${result.status}">${result.status.toUpperCase()}</span>
            </div>
            <div class="result-grid">
                <div class="result-item">
                    <div class="result-label">Cardholder Name</div>
                    <div class="result-value ${result.cardholder_name ? '' : 'missing'}">
                        ${result.cardholder_name || 'N/A'}
                    </div>
                </div>
                <div class="result-item">
                    <div class="result-label">Card Number (Last 4)</div>
                    <div class="result-value ${result.card_number ? '' : 'missing'}">
                        ${result.card_number ? '****' + result.card_number : 'N/A'}
                    </div>
                </div>
                <div class="result-item">
                    <div class="result-label">Credit Limit</div>
                    <div class="result-value ${result.credit_limit ? '' : 'missing'}">
                        ${result.credit_limit || 'N/A'}
                    </div>
                </div>
                <div class="result-item">
                    <div class="result-label">Total Due</div>
                    <div class="result-value ${result.total_due ? '' : 'missing'}">
                        ${result.total_due || 'N/A'}
                    </div>
                </div>
                <div class="result-item">
                    <div class="result-label">Payment Due Date</div>
                    <div class="result-value ${result.payment_due_date ? '' : 'missing'}">
                        ${result.payment_due_date || 'N/A'}
                    </div>
                </div>
            </div>
            ${result.errors ? `
                <div style="margin-top: 15px; color: #e74c3c;">
                    <strong>Errors:</strong>
                    <ul style="margin-left: 20px; margin-top: 5px;">
                        ${result.errors.map(err => `<li>${err}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
        </div>
    `).join('');
    
    // Show download section
    downloadSection.style.display = 'block';
    
    // Re-enable parse button
    parseBtn.disabled = false;
}

// Download File
async function downloadFile(format) {
    try {
        const response = await fetch(`/download/${format}`);
        
        if (!response.ok) {
            throw new Error('Download failed');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `parsed_statements.${format}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
    } catch (error) {
        alert(`Download failed: ${error.message}`);
    }
}