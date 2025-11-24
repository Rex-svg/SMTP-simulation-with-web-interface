// static/app.js
const API = {
  messages: "/api/messages",
  send: "/api/send",
};

const messagesEl = document.getElementById("messages");
const countEl = document.getElementById("count");
const messageView = document.getElementById("messageView");
const placeholder = document.querySelector(".placeholder");

async function fetchMessages() {
  try {
    const res = await fetch(API.messages);
    if (!res.ok) return;
    const msgs = await res.json();
    renderList(msgs);
  } catch (err) {
    console.error("Failed to fetch messages", err);
  }
}

function renderList(msgs) {
  messagesEl.innerHTML = "";
  countEl.textContent = `${msgs.length} messages`;
  if (msgs.length === 0) {
    messagesEl.innerHTML = "<li class='empty'>No messages</li>";
    return;
  }
  msgs.forEach(m => {
    const li = document.createElement("li");
    li.dataset.id = m.id;
    li.innerHTML = `
      <div class="msg-left">
        <div>
          <div class="msg-from">${escapeHtml(m.from || "unknown")}</div>
          <div class="msg-subject">${escapeHtml(m.subject || "(no subject)")}</div>
        </div>
      </div>
      <div class="msg-time">${new Date(m.received_at).toLocaleString()}</div>
    `;
    li.addEventListener("click", () => showMessage(m.id));
    messagesEl.appendChild(li);
  });
}

async function showMessage(id) {
  try {
    const res = await fetch(`/api/messages/${id}`);
    if (!res.ok) return;
    const m = await res.json();
    placeholder.classList.add("hidden");
    messageView.classList.remove("hidden");
    document.getElementById("m-subject").textContent = m.subject || "(no subject)";
    document.getElementById("m-from").textContent = m.from || "";
    document.getElementById("m-to").textContent = (m.to || []).join(", ");
    document.getElementById("m-date").textContent = new Date(m.received_at).toLocaleString();
    document.getElementById("m-body").textContent = m.body || "";
  } catch (err) {
    console.error("Failed to load message", err);
  }
}

function escapeHtml(text) {
  return String(text || "").replace(/[&<>"']/g, s => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":"&#39;"}[s]));
}

/* Compose panel behaviour (fixed left) */
const composeBtn = document.getElementById("composeBtn");
const composePanel = document.getElementById("composePanel");
const closeCompose = document.getElementById("closeCompose");
const sendBtn = document.getElementById("sendBtn");

composeBtn.addEventListener("click", () => toggleCompose(true));
closeCompose.addEventListener("click", () => toggleCompose(false));

function toggleCompose(show) {
  if (show === undefined) show = composePanel.classList.contains("hidden");
  if (show) {
    composePanel.classList.remove("hidden");
  } else {
    composePanel.classList.add("hidden");
    document.getElementById("composeStatus").textContent = "";
  }
}

sendBtn.addEventListener("click", async () => {
  const from = document.getElementById("c-from").value.trim();
  const to = document.getElementById("c-to").value.trim();
  const subject = document.getElementById("c-subject").value;
  const body = document.getElementById("c-body").value;
  const status = document.getElementById("composeStatus");
  if (!from || !to) {
    status.textContent = "From and To are required";
    return;
  }
  status.textContent = "Sending…";
  try {
    const res = await fetch(API.send, {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({from, to, subject, body})
    });
    const data = await res.json();
    if (res.ok) {
      status.textContent = "Sent ✅";
      // keep compose open for a moment then close:
      setTimeout(() => {
        toggleCompose(false);
      }, 500);
      await fetchMessages();
      // clear compose inputs
      document.getElementById("c-subject").value = "";
      document.getElementById("c-body").value = "";
      // do not clear 'from' so user can send multiple
    } else {
      status.textContent = data.error || "Failed to send";
    }
  } catch (err) {
    status.textContent = "Network error";
  }
});

/* Poll for new messages every 6 seconds */
fetchMessages();
setInterval(fetchMessages, 6000);
