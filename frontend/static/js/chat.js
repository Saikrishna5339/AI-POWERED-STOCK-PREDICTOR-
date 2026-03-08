/**
 * Chat module - AI chat assistant
 */

async function sendChat() {
  const input = document.getElementById('chatInput');
  const msg = input.value.trim();
  if (!msg) return;

  appendMessage(msg, 'user');
  input.value = '';

  const typingId = appendTyping();

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: msg }),
    });
    const data = await res.json();
    removeTyping(typingId);
    appendMessage(data.message || 'Sorry, I could not process that.', 'bot');
  } catch (e) {
    removeTyping(typingId);
    appendMessage('⚠️ Connection error. Make sure the server is running.', 'bot');
  }
}

function sendQuickMsg(msg) {
  document.getElementById('chatInput').value = msg;
  sendChat();
}

function handleChatKey(e) {
  if (e.key === 'Enter') sendChat();
}

function appendMessage(text, role) {
  const container = document.getElementById('chatMessages');
  const div = document.createElement('div');
  div.className = `chat-message ${role}`;

  // Format markdown-like bold
  const formatted = text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>');

  div.innerHTML = `
    <div class="msg-avatar">${role === 'user' ? '👤' : '🤖'}</div>
    <div class="msg-content">
      <div class="msg-bubble">${formatted}</div>
    </div>`;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function appendTyping() {
  const container = document.getElementById('chatMessages');
  const id = 'typing-' + Date.now();
  const div = document.createElement('div');
  div.id = id;
  div.className = 'chat-message bot';
  div.innerHTML = `
    <div class="msg-avatar">🤖</div>
    <div class="msg-content">
      <div class="msg-bubble" style="color:#64748b">
        <span style="animation:pulse 1s infinite">Analyzing</span>...
      </div>
    </div>`;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  return id;
}

function removeTyping(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

// Global exports
window.sendChat = sendChat;
window.sendQuickMsg = sendQuickMsg;
window.handleChatKey = handleChatKey;

