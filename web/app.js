const gateEl = document.getElementById("gate");
const appEl = document.getElementById("app");
const gateError = document.getElementById("gateError");
const googleBtn = document.getElementById("googleBtn");
const messagesEl = document.getElementById("messages");
const composer = document.getElementById("composer");
const input = document.getElementById("input");
const sendBtn = document.getElementById("send");
const chipsEl = document.getElementById("chips");
const ticketEl = document.getElementById("ticket");
const pulseEl = document.getElementById("pulse");
const vibeCardEl = document.getElementById("vibeCard");
const sidePanel = document.getElementById("sidePanel");
const userChip = document.getElementById("userChip");
const userPic = document.getElementById("userPic");
const userInitial = document.getElementById("userInitial");
const userName = document.getElementById("userName");
const accountBtn = document.getElementById("accountBtn");
const accountMenu = document.getElementById("accountMenu");
const swiggyBtn = document.getElementById("swiggyBtn");
const logoutBtn = document.getElementById("logout");
const sheetPeek = document.getElementById("sheetPeek");
const sheetPeekLabel = document.getElementById("sheetPeekLabel");
const sheetScrim = document.getElementById("sheetScrim");
const sideSheet = document.getElementById("sideSheet");
const sheetBody = document.getElementById("sheetBody");
const sheetClose = document.getElementById("sheetClose");

const SUGGESTIONS = [
  "Let’s do my vibe check",
  "Something cozy, not too sweet",
  "Who matches my vibe?",
  "How’s the room looking?",
];

let busy = false;
let currentUser = null;
let hasTicket = false;

function autoGrow() {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 120)}px`;
}

function escapeHtml(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function renderMarkdown(src) {
  const escaped = escapeHtml(src.replace(/\r\n/g, "\n").trim());
  const blocks = escaped.split(/\n{2,}/);
  return (
    blocks
      .map((block) => {
        const lines = block.split("\n");
        const isList = lines.every(
          (line) => /^[-*•]\s+/.test(line.trim()) || !line.trim()
        );
        if (isList && lines.some((line) => /^[-*•]\s+/.test(line.trim()))) {
          const items = lines
            .filter((line) => /^[-*•]\s+/.test(line.trim()))
            .map(
              (line) =>
                `<li>${inlineMarkdown(line.trim().replace(/^[-*•]\s+/, ""))}</li>`
            )
            .join("");
          return `<ul>${items}</ul>`;
        }
        return `<p>${inlineMarkdown(lines.join("<br>"))}</p>`;
      })
      .join("") || "<p></p>"
  );
}

function inlineMarkdown(text) {
  return text
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/__([^_]+)__/g, "<strong>$1</strong>")
    .replace(/(^|[\s(])\*([^*\n]+)\*(?=[\s).,!?:;]|$)/g, "$1<em>$2</em>")
    .replace(/(^|[\s(])_([^_\n]+)_(?=[\s).,!?:;]|$)/g, "$1<em>$2</em>");
}

function addMessage(role, text, { thinking = false } = {}) {
  const row = document.createElement("div");
  row.className = `msg ${role}${thinking ? " thinking" : ""}`;

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = role === "user" ? "You" : "AI";

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  if (role === "assistant" && !thinking) {
    bubble.classList.add("md");
    bubble.innerHTML = renderMarkdown(text);
  } else {
    bubble.textContent = text;
  }

  row.append(avatar, bubble);
  messagesEl.appendChild(row);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return { row, bubble };
}

function renderChips() {
  chipsEl.innerHTML = "";
  for (const label of SUGGESTIONS) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "chip";
    btn.textContent = label;
    btn.addEventListener("click", () => {
      input.value = label;
      autoGrow();
      input.focus();
      composer.requestSubmit();
    });
    chipsEl.appendChild(btn);
  }
}

function extractToolPayloads(events) {
  const payloads = [];
  for (const event of events || []) {
    for (const part of event.content?.parts || []) {
      const fr = part.functionResponse;
      if (fr?.response) payloads.push({ name: fr.name, response: fr.response });
    }
  }
  return payloads;
}

function refreshSheetBody() {
  if (!sheetBody || !sidePanel) return;
  sheetBody.innerHTML = sidePanel.innerHTML;
}

function setSheetPeekState() {
  if (!sheetPeek) return;
  sheetPeek.classList.toggle("has-ticket", hasTicket);
  if (sheetPeekLabel) {
    sheetPeekLabel.textContent = hasTicket ? "View live ticket" : "Ticket & pulse";
  }
}

function openSheet() {
  if (!sideSheet || !sheetScrim || !sheetPeek) return;
  if (window.matchMedia("(min-width: 720px)").matches) return;
  refreshSheetBody();
  sideSheet.hidden = false;
  sheetScrim.hidden = false;
  sheetPeek.setAttribute("aria-expanded", "true");
  sheetClose?.focus();
}

function closeSheet() {
  if (!sideSheet || !sheetScrim || !sheetPeek) return;
  sideSheet.hidden = true;
  sheetScrim.hidden = true;
  sheetPeek.setAttribute("aria-expanded", "false");
}

function updateTicket(order) {
  if (!order || order.status === "error") return;
  ticketEl.classList.remove("empty");
  const items = (order.items || [])
    .map(
      (item) =>
        `<li>${escapeHtml(item.name)}${
          order.mods ? ` · ${escapeHtml(order.mods)}` : ""
        }</li>`
    )
    .join("");
  ticketEl.innerHTML = `
    <div class="id">${escapeHtml(order.order_id || "Ticket")}</div>
    <p class="meta">${escapeHtml(order.guest_name || "Guest")} · ~${
      order.eta_minutes ?? "?"
    } min</p>
    <p class="meta">${escapeHtml(order.pickup || "Counter pickup")}</p>
    <ul>${items || "<li>Order placed</li>"}</ul>
  `;
  hasTicket = true;
  setSheetPeekState();
  refreshSheetBody();
  if (!window.matchMedia("(min-width: 720px)").matches) openSheet();
}

function updatePulse(pulse) {
  if (!pulse || pulse.status === "error") return;
  pulseEl.classList.remove("empty");
  pulseEl.dataset.crowd = pulse.crowd || "steady";
  pulseEl.innerHTML = `
    <div class="crowd">${escapeHtml(pulse.crowd || "steady")} · ~${
      pulse.avg_wait_minutes ?? "?"
    } min wait</div>
    <p>${escapeHtml(pulse.guest_tip || "")}</p>
    <p><strong>Baristas:</strong> ${escapeHtml(pulse.staff_tip || "")}</p>
  `;
  refreshSheetBody();
}

function updatePersonality(personality) {
  if (!personality || !vibeCardEl) return;
  vibeCardEl.classList.remove("empty");
  const tags = (personality.tags || [])
    .slice(0, 6)
    .map((t) => `<span class="vibe-tag">${escapeHtml(t)}</span>`)
    .join("");
  vibeCardEl.innerHTML = `
    <p class="vibe-label">${escapeHtml(personality.label || "Café personality")}</p>
    <p class="vibe-blurb">${escapeHtml(personality.blurb || "")}</p>
    <p class="vibe-hint">${escapeHtml(personality.drink_hint || "")}</p>
    <div class="vibe-tags">${tags}</div>
  `;
  refreshSheetBody();
}

function renderVibeOptions(question) {
  if (!question?.options?.length || !chipsEl) return;
  chipsEl.innerHTML = "";
  chipsEl.setAttribute("aria-label", question.prompt || "Vibe options");
  for (const opt of question.options) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "chip vibe-option";
    const key = opt.choice_key || "";
    btn.textContent = `${opt.emoji || ""} ${key ? `${key}. ` : ""}${opt.label}`.trim();
    const payload = `${opt.label}`;
    btn.addEventListener("click", () => {
      input.value = payload;
      autoGrow();
      composer.requestSubmit();
    });
    chipsEl.appendChild(btn);
  }
}

function applyToolSideEffects(events) {
  for (const { name, response } of extractToolPayloads(events)) {
    if (name === "place_order" && response?.status === "success") updateTicket(response);
    if (name === "get_room_pulse" && response?.status === "success") updatePulse(response);
    if (
      (name === "start_vibe_check" || name === "answer_vibe_question") &&
      response?.status === "success"
    ) {
      if (response.question) renderVibeOptions(response.question);
      if (response.personality) {
        updatePersonality(response.personality);
        renderChips();
      }
    }
    if (name === "get_my_profile" && response?.personality) {
      updatePersonality(response.personality);
    }
  }
}

function showGate(message = "") {
  gateEl.hidden = false;
  appEl.hidden = true;
  closeSheet();
  closeAccountMenu();
  if (message) {
    gateError.hidden = false;
    gateError.textContent = message;
  } else {
    gateError.hidden = true;
  }
}

function setSwiggyUi(swiggy) {
  if (!swiggyBtn) return;
  const connected = Boolean(swiggy?.connected) && !swiggy?.token_expired;
  swiggyBtn.dataset.connected = connected ? "1" : "0";
  swiggyBtn.textContent = connected ? "Disconnect Swiggy" : "Connect Swiggy";
  swiggyBtn.title = connected
    ? "Disconnect Swiggy Food MCP"
    : "Connect Swiggy Food MCP (OAuth)";
}

function closeAccountMenu() {
  if (!accountMenu || !accountBtn) return;
  accountMenu.hidden = true;
  accountBtn.setAttribute("aria-expanded", "false");
}

function toggleAccountMenu() {
  if (!accountMenu || !accountBtn) return;
  const open = accountMenu.hidden;
  accountMenu.hidden = !open;
  accountBtn.setAttribute("aria-expanded", open ? "true" : "false");
}

function showApp(user, swiggy) {
  currentUser = user;
  gateEl.hidden = true;
  appEl.hidden = false;
  userChip.hidden = false;
  const label = user.name || user.email || "Guest";
  userName.textContent = label;
  if (user.picture) {
    userPic.src = user.picture;
    userPic.hidden = false;
    userInitial.hidden = true;
  } else {
    userPic.hidden = true;
    userInitial.hidden = false;
    userInitial.textContent = (label.trim()[0] || "G").toUpperCase();
  }
  setSwiggyUi(swiggy);
  setSheetPeekState();
  if (user.personality) updatePersonality(user.personality);
  if (!messagesEl.childElementCount) {
    const vibeLine = user.personality
      ? `You’re vibing as **${user.personality.label}** — ask for a drink tip or who matches your energy.`
      : `First, let’s get your **café vibe** — tap *Let’s do my vibe check* (quirky movie / playlist picks).`;
    addMessage(
      "assistant",
      `Hi ${user.name || "there"} — welcome to Café Concierge at Third Wave Kondapur.\n\n${vibeLine}\n\nAvatar menu → **Connect Swiggy** for delivery discovery.`
    );
  }
  if (Array.isArray(user.recent_orders) && user.recent_orders[0]) {
    updateTicket({
      ...user.recent_orders[0],
      pickup: "Counter — Third Wave Kondapur",
    });
  }
  input.focus();
}

async function handleGoogleCredential(response) {
  try {
    const res = await fetch("/api/auth/google", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ credential: response.credential }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Sign-in failed");
    showApp({ ...data.user, recent_orders: [] }, null);
    const me = await fetch("/api/me").then((r) => r.json());
    if (me.authenticated) {
      showApp({ ...me.user, recent_orders: me.recent_orders }, me.swiggy);
    }
  } catch (err) {
    showGate(err.message);
  }
}

function initGoogleButton(clientId) {
  const mount = () => {
    if (!window.google?.accounts?.id) {
      setTimeout(mount, 100);
      return;
    }
    window.google.accounts.id.initialize({
      client_id: clientId,
      callback: handleGoogleCredential,
      auto_select: false,
      cancel_on_tap_outside: true,
    });
    googleBtn.innerHTML = "";
    const width = Math.min(320, Math.max(260, window.innerWidth - 64));
    window.google.accounts.id.renderButton(googleBtn, {
      theme: "outline",
      size: "large",
      shape: "pill",
      text: "signin_with",
      width,
    });
  };
  mount();
}

function consumeSwiggyQuery() {
  const params = new URLSearchParams(window.location.search);
  const status = params.get("swiggy");
  if (!status) return;
  const reason = params.get("reason") || "";
  history.replaceState({}, "", "/");
  if (status === "connected") {
    addMessage(
      "assistant",
      "Swiggy Food MCP is connected. Ask me to find restaurants or dishes near Kondapur."
    );
  } else if (status === "error") {
    addMessage(
      "assistant",
      `Swiggy connect failed${reason ? `: ${reason}` : ""}. Try Connect Swiggy again from your avatar menu.`
    );
  }
}

async function bootstrap() {
  renderChips();
  const config = await fetch("/api/config").then((r) => r.json());
  if (!config.auth_configured) {
    showGate(
      "Add GOOGLE_CLIENT_ID to .env.local (Google Cloud → Credentials → OAuth client ID → Web). Origins must include http://localhost:5173."
    );
    return;
  }

  const me = await fetch("/api/me").then((r) => r.json());
  if (me.authenticated) {
    showApp({ ...me.user, recent_orders: me.recent_orders }, me.swiggy);
    consumeSwiggyQuery();
  } else {
    showGate();
  }
  initGoogleButton(config.google_client_id);
}

accountBtn?.addEventListener("click", (e) => {
  e.stopPropagation();
  toggleAccountMenu();
});

document.addEventListener("click", (e) => {
  if (!userChip?.contains(e.target)) closeAccountMenu();
});

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    closeAccountMenu();
    closeSheet();
  }
});

sheetPeek?.addEventListener("click", () => {
  if (sideSheet?.hidden) openSheet();
  else closeSheet();
});

sheetClose?.addEventListener("click", closeSheet);
sheetScrim?.addEventListener("click", closeSheet);

swiggyBtn?.addEventListener("click", async () => {
  closeAccountMenu();
  if (swiggyBtn.dataset.connected === "1") {
    const res = await fetch("/api/swiggy/disconnect", { method: "POST" });
    const data = await res.json();
    if (res.ok) {
      setSwiggyUi(data.swiggy);
      addMessage("assistant", "Swiggy disconnected. Pop-Up café tools still work.");
    }
    return;
  }
  window.location.href = "/api/swiggy/connect";
});

async function sendMessage(text) {
  const trimmed = text.trim();
  if (!trimmed || busy) return;

  busy = true;
  sendBtn.disabled = true;
  addMessage("user", trimmed);
  input.value = "";
  autoGrow();
  const thinking = addMessage("assistant", "Thinking…", { thinking: true });

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: trimmed }),
    });
    const data = await res.json();
    if (res.status === 401) {
      thinking.row.remove();
      showGate("Please sign in with Google again.");
      return;
    }
    if (!res.ok) {
      const detail = data.detail || data.error || "Request failed";
      throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }

    thinking.row.remove();
    addMessage("assistant", data.reply || "Done.");
    applyToolSideEffects(data.events || []);
  } catch (err) {
    thinking.row.remove();
    addMessage(
      "assistant",
      `Something went wrong: ${err.message}. Check the server is running with Vertex credentials.`
    );
  } finally {
    busy = false;
    sendBtn.disabled = false;
    input.focus();
  }
}

composer.addEventListener("submit", (e) => {
  e.preventDefault();
  sendMessage(input.value);
});

input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    composer.requestSubmit();
  }
});

input.addEventListener("input", autoGrow);

logoutBtn.addEventListener("click", async () => {
  closeAccountMenu();
  await fetch("/api/logout", { method: "POST" });
  messagesEl.innerHTML = "";
  currentUser = null;
  hasTicket = false;
  setSheetPeekState();
  showGate();
});

bootstrap();
