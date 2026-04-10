// ==================== API ENDPOINTS (Flask backend) ====================
const API = {
    upload: '/api/upload',
    chat: '/api/chat',
    fileInfo: '/api/file-info'
};

// ==================== DOM ELEMENTS ====================
const fileInput = document.getElementById('fileInput');
const uploadArea = document.getElementById('uploadArea');
const uploadBtn = document.getElementById('uploadBtn');
const uploadStatus = document.getElementById('uploadStatus');
const fileInfo = document.getElementById('fileInfo');
const refreshFileInfoBtn = document.getElementById('refreshFileInfoBtn');
const questionInput = document.getElementById('questionInput');
const sendBtn = document.getElementById('sendBtn');
const chatMessages = document.getElementById('chatMessages');
const chatStatus = document.getElementById('chatStatus');

// ==================== STATE ====================
let documentLoaded = false;
let selectedFiles = []; // Maintained separately since FileList is read-only

// ==================== UPLOAD FUNCTIONALITY ====================

// Click to select file
uploadArea.addEventListener('click', () => fileInput.click());

// File selected through input
fileInput.addEventListener('change', () => {
    // Merge newly picked files into selectedFiles (skip duplicates by name+size)
    Array.from(fileInput.files).forEach(file => {
        if (!selectedFiles.find(f => f.name === file.name && f.size === file.size)) {
            selectedFiles.push(file);
        }
    });
    syncFilesToInput();
    updateUploadStatusDisplay();
});

// Sync selectedFiles array back into the hidden file input
function syncFilesToInput() {
    const dt = new DataTransfer();
    selectedFiles.forEach(file => dt.items.add(file));
    fileInput.files = dt.files;
}

// Remove a file by index from the selection
function removeFile(index) {
    selectedFiles.splice(index, 1);
    syncFilesToInput();
    updateUploadStatusDisplay();
}

// File type icons
function getFileIcon(ext) {
    const icons = { pdf: '📄', docx: '📝', doc: '📝', txt: '📃', md: '📋' };
    return icons[ext] || '📁';
}

// Render selected files inside the drop zone
function updateUploadStatusDisplay() {
    const dropText = uploadArea.querySelector('.drop-text');
    const filesList = document.getElementById('selectedFilesList');
    const count = selectedFiles.length;

    if (count === 0) {
        dropText.style.display = 'block';
        filesList.style.display = 'none';
        filesList.innerHTML = '';
        uploadBtn.disabled = true;
        uploadBtn.textContent = 'Upload File';
        return;
    }

    dropText.style.display = 'none';
    filesList.style.display = 'block';

    const totalSize = selectedFiles.reduce((sum, f) => sum + f.size, 0);
    const totalMB = (totalSize / (1024 * 1024)).toFixed(2);

    filesList.innerHTML = `
        <div class="files-list-header">
            <span>${count} file${count > 1 ? 's' : ''} selected &nbsp;•&nbsp; ${totalMB} MB total</span>
            <button class="clear-all-btn" onclick="clearAllFiles()">Clear all</button>
        </div>
        ${selectedFiles.map((file, i) => {
            const ext = file.name.split('.').pop().toLowerCase();
            const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
            return `
                <div class="file-item">
                    <span class="file-item-icon">${getFileIcon(ext)}</span>
                    <span class="file-item-name" title="${file.name}">${file.name}</span>
                    <span class="file-item-size">${sizeMB} MB</span>
                    <button class="file-remove-btn" onclick="removeFile(${i})" title="Remove file">✕</button>
                </div>`;
        }).join('')}
        <div class="add-more-hint" onclick="fileInput.click()">＋ Add more files</div>
    `;

    uploadBtn.disabled = false;
    uploadBtn.textContent = count > 1 ? `Upload ${count} Files` : 'Upload File';
}

// Clear all selected files
function clearAllFiles() {
    selectedFiles = [];
    syncFilesToInput();
    updateUploadStatusDisplay();
}

// Drag and drop
uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    // Merge dropped files into selectedFiles (skip duplicates)
    Array.from(e.dataTransfer.files).forEach(file => {
        if (!selectedFiles.find(f => f.name === file.name && f.size === file.size)) {
            selectedFiles.push(file);
        }
    });
    syncFilesToInput();
    updateUploadStatusDisplay();
});

// Upload file
uploadBtn.addEventListener('click', uploadFile);

async function uploadFile() {
    if (!fileInput.files.length) {
        showStatus('uploadStatus', 'Please select a file first', 'error');
        return;
    }

    const isMultiple = fileInput.files.length > 1;
    const formData = new FormData();

    // Flask: always use 'file' field name (works for single and multiple)
    for (let i = 0; i < fileInput.files.length; i++) {
        formData.append('file', fileInput.files[i]);
    }

    uploadBtn.disabled = true;
    const fileCount = fileInput.files.length;
    const msg = isMultiple ? `Uploading and parsing ${fileCount} files...` : 'Uploading and parsing file...';
    showStatus('uploadStatus', msg, 'loading');

    try {
        const response = await fetch(API.upload, {
            method: 'POST',
            body: formData
        });

        // Get response text first to debug
        const text = await response.text();
        console.log('Raw response:', text);
        console.log('Response status:', response.status);

        if (!text) {
            throw new Error('Empty response from server');
        }

        // Parse as JSON
        let data;
        try {
            data = JSON.parse(text);
        } catch (e) {
            console.error('Failed to parse JSON:', text);
            throw new Error('Invalid JSON response: ' + e.message);
        }

        // Check response status regardless of HTTP status
        if (!data.success) {
            showStatus('uploadStatus', 'Upload failed: ' + (data.message || 'Unknown error'), 'error');
            console.error('Server error:', data);
            uploadBtn.disabled = false;
            return;
        }

        // Success!
        let successMsg = data.message || 'File uploaded and parsed successfully!';
        if (isMultiple && data.data && data.data.uploadedCount) {
            successMsg = `${data.data.uploadedCount} files uploaded and combined successfully!`;
        }

        showStatus('uploadStatus', successMsg, 'success');
        documentLoaded = true;

        // Log response data
        console.log('Upload response:', data.data);

        // Enable chat
        questionInput.disabled = false;
        sendBtn.disabled = false;

        // Clear chat messages
        const chatMsg = isMultiple && data.data && data.data.uploadedCount
            ? `${data.data.uploadedCount} documents combined and loaded! You can now ask questions.`
            : 'Document loaded! You can now ask questions.';
        chatMessages.innerHTML = `<div class="system-message">${chatMsg}</div>`;
        
        // Refresh file info
        await refreshFileInfo();
        
        // Reset upload input and file list
        selectedFiles = [];
        syncFilesToInput();
        updateUploadStatusDisplay();

    } catch (error) {
        console.error('Upload error:', error);
        showStatus('uploadStatus', 'Error: ' + error.message, 'error');
        uploadBtn.disabled = false;
    }
}

// ==================== FILE INFO ====================

refreshFileInfoBtn.addEventListener('click', refreshFileInfo);

async function refreshFileInfo() {
    try {
        const response = await fetch(API.fileInfo);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const text = await response.text();
        if (!text) {
            throw new Error('Empty response from server');
        }

        const data = JSON.parse(text);

        if (!data.success) {
            fileInfo.innerHTML = '<p class="placeholder">Unable to load file info</p>';
            return;
        }

        let html = '';

        if (data.data.uploaded) {
            const u = data.data.uploaded;
            html += `
                <div class="file-info-item">
                    <span class="file-info-label">📤 Uploaded File:</span>
                    <span class="file-info-value">${u.filename}</span>
                </div>
                <div class="file-info-item">
                    <span class="file-info-label">Format:</span>
                    <span class="file-info-value">.${u.extension}</span>
                </div>
                <div class="file-info-item">
                    <span class="file-info-label">Size:</span>
                    <span class="file-info-value">${u.size}</span>
                </div>
                <div class="file-info-item">
                    <span class="file-info-label">Uploaded:</span>
                    <span class="file-info-value">${u.uploadTime}</span>
                </div>
            `;
        }

        if (data.data.parsed) {
            const p = data.data.parsed;
            html += `
                <div class="file-info-item">
                    <span class="file-info-label">✅ Parsed File:</span>
                    <span class="file-info-value">${p.filename}</span>
                </div>
            `;
            
            // Display parsed content section
            displayParsedContent(p.content);
        }

        if (!html) {
            html = '<p class="placeholder">No document uploaded yet</p>';
        }

        fileInfo.innerHTML = html;

    } catch (error) {
        console.error('Error refreshing file info:', error);
        fileInfo.innerHTML = '<p class="placeholder">Error loading file info</p>';
    }
}

// Display parsed text content
function displayParsedContent(content) {
    const parsedSection = document.querySelector('.parsed-text-section');
    const parsedContentDiv = document.getElementById('parsedContent');
    
    if (parsedSection && parsedContentDiv) {
        // Clear placeholder if it exists
        if (parsedContentDiv.querySelector('.placeholder')) {
            parsedContentDiv.innerHTML = '';
        }
        parsedContentDiv.textContent = content;
        parsedSection.style.display = 'block';
        
        // Scroll to the section
        setTimeout(() => {
            parsedSection.scrollIntoView({ behavior: 'smooth' });
        }, 100);
    }
}

// Copy parsed text to clipboard
document.addEventListener('DOMContentLoaded', () => {
    const copyBtn = document.getElementById('copyParsedBtn');
    if (copyBtn) {
        copyBtn.addEventListener('click', () => {
            const parsedContentDiv = document.getElementById('parsedContent');
            if (parsedContentDiv) {
                const text = parsedContentDiv.textContent;
                navigator.clipboard.writeText(text).then(() => {
                    showStatus('chatStatus', 'Parsed text copied to clipboard!', 'success');
                    setTimeout(() => {
                        chatStatus.textContent = '';
                    }, 2000);
                }).catch(err => {
                    console.error('Failed to copy:', err);
                    showStatus('chatStatus', 'Failed to copy text', 'error');
                });
            }
        });
    }
});

// ==================== CHAT FUNCTIONALITY ====================

sendBtn.addEventListener('click', sendQuestion);
questionInput.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'Enter') {
        sendQuestion();
    }
});

async function sendQuestion() {
    const question = questionInput.value.trim();

    if (!question) {
        showStatus('chatStatus', 'Please enter a question', 'error');
        return;
    }

    if (!documentLoaded) {
        showStatus('chatStatus', 'Please upload a document first', 'error');
        return;
    }

    // Add user message to chat
    addMessageToChat(question, 'user');
    questionInput.value = '';
    questionInput.focus();

    // Show loading message
    const loadingId = addMessageToChat('Getting answer...', 'ai-loading');

    sendBtn.disabled = true;

    try {
        const response = await fetch(API.chat, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ question })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const text = await response.text();
        if (!text) {
            throw new Error('Empty response from server');
        }

        let data;
        try {
            data = JSON.parse(text);
        } catch (e) {
            console.error('Failed to parse JSON:', text);
            throw new Error('Invalid JSON response: ' + e.message);
        }

        // Remove loading message
        removeLoadingMessage(loadingId);

        if (!data.success) {
            addMessageToChat('Error: ' + (data.error || data.message || 'Unknown error'), 'ai');
            return;
        }

        addMessageToChat(data.answer, 'ai');

    } catch (error) {
        console.error('Chat error:', error);
        removeLoadingMessage(loadingId);
        addMessageToChat('Error: ' + error.message, 'ai');
    } finally {
        sendBtn.disabled = false;
    }
}

function addMessageToChat(message, type) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'chat-message';
    
    if (type === 'user') {
        messageDiv.classList.add('user-message');
    } else if (type === 'ai-loading') {
        messageDiv.classList.add('ai-message', 'loading-message');
        messageDiv.id = 'loading-' + Date.now();
        message = '<span class="spinner"></span> ' + message;
    } else {
        messageDiv.classList.add('ai-message');
    }

    messageDiv.innerHTML = message;
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return messageDiv.id;
}

function removeLoadingMessage(loadingId) {
    const element = document.getElementById(loadingId);
    if (element) {
        element.remove();
    }
}

// ==================== HELPER FUNCTIONS ====================

function showStatus(elementId, message, type) {
    const element = document.getElementById(elementId);
    element.textContent = message;
    element.className = 'status-message show ' + type;

    // Auto-hide success and info messages after 5 seconds
    if (type === 'success' || type === 'info') {
        setTimeout(() => {
            element.classList.remove('show');
        }, 5000);
    }
}

// ==================== INITIALIZATION ====================

document.addEventListener('DOMContentLoaded', () => {
    refreshFileInfo();
});
