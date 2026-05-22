(function () {
  const SESSION_KEY = "chat_session_id";

  const toggle = document.getElementById("chat-toggle");
  const widget = document.getElementById("chat-widget");
  const messages = document.getElementById("chat-messages");
  const footer = document.getElementById("chat-footer");
  const input = document.getElementById("chat-input");
  const sendBtn = document.getElementById("chat-send");
  const closedMsg = document.getElementById("chat-closed-msg");

  let sessionId = null;
  let isStreaming = false;

  toggle.addEventListener("click", async () => {
    const opening = widget.classList.contains("d-none");
    widget.classList.toggle("d-none");
    if (opening && !sessionId) {
      await initSession();
      await sendGreeting();
    } else if (!opening) {
      sessionStorage.removeItem(SESSION_KEY);
      sessionId = null;
      messages.innerHTML = "";
      closedMsg.classList.add("d-none");
      footer.classList.remove("d-none");
    }
  });

  async function initSession() {
    const stored = sessionStorage.getItem(SESSION_KEY);
    if (stored) {
      sessionId = stored;
      return;
    }
    const res = await fetch("/api/chat/session", { method: "POST" });
    const data = await res.json();
    sessionId = data.session_id;
    sessionStorage.setItem(SESSION_KEY, sessionId);
  }

  async function sendGreeting() {
    setDisabled(true);
    const bubble = appendBubble("assistant", "");
    try {
      const res = await fetch("/api/chat/message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, message: "__greet__" }),
      });
      await readStream(res, bubble);
    } catch (e) {
      bubble.textContent = "Hi! I'm Jessica. How can I help you?";
    }
    setDisabled(false);
  }

  sendBtn.addEventListener("click", sendMessage);
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  async function sendMessage() {
    const text = input.value.trim();
    if (!text || isStreaming) return;

    appendBubble("user", text);
    input.value = "";
    setDisabled(true);

    const bubble = appendBubble("assistant", "");

    try {
      const res = await fetch("/api/chat/message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, message: text }),
      });
      await readStream(res, bubble);
    } catch (e) {
      bubble.textContent = "Something went wrong. Please try again.";
    }

    setDisabled(false);
  }

  async function readStream(res, bubble) {
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n\n");
      buffer = lines.pop();

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        const payload = line.slice(6).trim();
        if (payload === "[DONE]") break;

        const parsed = JSON.parse(payload);
        if (parsed.token) {
          bubble.textContent += parsed.token;
          messages.scrollTop = messages.scrollHeight;
        } else if (parsed.event === "chat_complete") {
          sessionStorage.removeItem(SESSION_KEY);
          closeLead();
        } else if (parsed.event === "error") {
          bubble.textContent = "I'm sorry, something went wrong. Please try again or call us directly.";
        }
      }
    }
  }

  function appendBubble(role, text) {
    const div = document.createElement("div");
    div.className = `chat-bubble ${role}`;
    div.textContent = text;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
    return div;
  }

  function setDisabled(val) {
    isStreaming = val;
    sendBtn.disabled = val;
    input.disabled = val;
  }

  function closeLead() {
    footer.classList.add("d-none");
    closedMsg.classList.remove("d-none");
  }

  document.getElementById("chat-new").addEventListener("click", async () => {
    sessionStorage.removeItem(SESSION_KEY);
    sessionId = null;
    messages.innerHTML = "";
    closedMsg.classList.add("d-none");
    footer.classList.remove("d-none");
    await initSession();
  });
})();