

let sessionId = null;
let currentPlaceholder = null;
let collectedValues = {};

// File upload handler
document.getElementById('fileInput').addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        showLoading('Analyzing document...');
        
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();

        if (!response.ok) throw new Error(data.detail);

        sessionId = data.session_id;
        currentPlaceholder = data.current_placeholder;

        document.getElementById('upload-section').classList.add('hidden');
        document.getElementById('chat-section').classList.remove('hidden');

        document.getElementById('userInput').disabled = false;
        document.getElementById('sendBtn').disabled = false;

        addMessage(data.first_question, 'assistant');

        // Update progress - handle both formats
        if (data.progress) {
            const [current, total] = data.progress.split('/');
            updateProgress(parseInt(current), parseInt(total));
        } else {
            // Fallback if progress not in response
            updateProgress(1, data.total_placeholders);
        }
        
    } catch (error) {
        alert('Error: ' + error.message);
    }
});

async function sendMessage() {
    const input = document.getElementById('userInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Display user message
    addMessage(message, 'user');
    input.value = '';
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: sessionId,
                message: message,
                placeholder: currentPlaceholder
            })
        });
        
        const data = await response.json();
        
        if (data.type === 'validation_error') {
            addMessage(data.message, 'assistant');
        } else if (data.type === 'next_question') {
            currentPlaceholder = data.current_placeholder;
            addMessage(data.question, 'assistant');
            updateProgress(...data.progress.split('/'));
        } else if (data.type === 'complete') {
            addMessage(data.message, 'assistant');
            await generateDocumentPreview();
        }
        
    } catch (error) {
        addMessage('Error: ' + error.message, 'assistant');
    }
}

async function generateDocumentPreview() {
    try {
        addMessage('Generating your document preview...', 'assistant');
        
        const response = await fetch('/api/generate?session_id=' + sessionId, {
            method: 'POST'
        });
        
        const data = await response.json();
        collectedValues = data.collected_values;
        
        // Switch to preview section
        document.getElementById('chat-section').classList.add('hidden');
        document.getElementById('preview-section').classList.remove('hidden');
        
        // Display preview
        document.getElementById('document-preview').innerHTML = data.preview_html;
        
        // Setup download button
        document.getElementById('downloadBtn').onclick = () => {
            window.location.href = `/api/download/${sessionId}`;
        };
        
    } catch (error) {
        alert('Error generating document: ' + error.message);
    }
}

function showEditModal() {
    const modal = document.getElementById('editModal');
    const form = document.getElementById('editForm');
    
    // Generate edit form
    form.innerHTML = '';
    for (const [key, value] of Object.entries(collectedValues)) {
        const fieldDiv = document.createElement('div');
        fieldDiv.className = 'edit-field';
        fieldDiv.innerHTML = `
            <label>${formatPlaceholderName(key)}</label>
            <input type="text" id="edit_${key}" value="${value}" data-key="${key}">
        `;
        form.appendChild(fieldDiv);
    }
    
    modal.classList.remove('hidden');
}

function closeEditModal() {
    document.getElementById('editModal').classList.add('hidden');
}


async function saveEdits() {
    const form = document.getElementById('editForm');
    const inputs = form.querySelectorAll('input');
    
    const updatedValues = {};
    inputs.forEach(input => {
        const key = input.dataset.key;
        const value = input.value.trim();
        updatedValues[key] = value;
        console.log(`Updated: ${key} = ${value}`);
    });
    
    console.log('Sending updated values:', updatedValues);
    
    try {
        const response = await fetch(`/api/update-values?session_id=${sessionId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updatedValues)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Update failed');
        }
        
        const data = await response.json();
        
        console.log('Update response:', data);
        
        // Update preview
        document.getElementById('document-preview').innerHTML = data.preview_html;
        
        // Update local collectedValues
        collectedValues = data.collected_values || updatedValues;
        
        closeEditModal();
        
        // Show success message
        alert('Document updated successfully!');
        
    } catch (error) {
        console.error('Update error:', error);
        alert('Error updating document: ' + error.message);
    }
}


function formatPlaceholderName(name) {
    // Convert placeholder names to readable format
    return name
        .replace(/_/g, ' ')
        .replace(/\b\w/g, l => l.toUpperCase());
}

function addMessage(text, sender) {
    const container = document.getElementById('chat-container');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.textContent = text;
    
    messageDiv.appendChild(bubble);
    container.appendChild(messageDiv);
    
    container.scrollTop = container.scrollHeight;
}

function updateProgress(current, total) {
    const percent = (current / total) * 100;
    document.getElementById('progress').style.width = percent + '%';
    document.getElementById('progress-text').textContent = `${current}/${total}`;
}

function showLoading(message) {
    addMessage(message, 'assistant');
}

document.getElementById('userInput').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});

document.getElementById('editModal').addEventListener('click', (e) => {
    if (e.target.id === 'editModal') {
        closeEditModal();
    }
});
