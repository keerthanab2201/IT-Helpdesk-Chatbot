// static/script.js
document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('#chat-form');
    const input = document.querySelector('#user-input');
    const chatBox = document.querySelector('#chat-box');

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        const message = input.value.trim();
        
        if (message) {
            // Add user message to chat
            chatBox.innerHTML += `<div class="user-message">${message}</div>`;
            
            // Send to backend
            fetch('/get_response', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    conversation: [{role: "user", content: message}]
                })
            })
            .then(response => response.json())
            .then(data => {
                // Add bot response to chat
                chatBox.innerHTML += `<div class="bot-message">${data}</div>`;
                input.value = ''; // Clear input
                chatBox.scrollTop = chatBox.scrollHeight; // Auto-scroll
            })
            .catch(error => {
                console.error('Error:', error);
                chatBox.innerHTML += `<div class="bot-message error">Sorry, I encountered an error.</div>`;
            });
        }
    });
});