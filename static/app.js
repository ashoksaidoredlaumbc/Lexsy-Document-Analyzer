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
