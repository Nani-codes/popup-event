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
const vibeBanner = document.getElementById("vibeBanner");
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
const matchesListEl = document.getElementById("matchesList");
const matchToast = document.getElementById("matchToast");
const matchToastMsg = document.getElementById("matchToastMsg");
const matchToastDismiss = document.getElementById("matchToastDismiss");

const SUGGESTIONS = [
  "Something cozy, not too sweet",
  "Who matches my vibe?",
  "Show my matches",
  "How’s the room looking?",
];

let busy = false;
let currentUser = null;
let hasTicket = false;
let vibeRequired = false;
let currentVibeQuestion = null;
let vibeBootstrapped = false;
let notifyPollTimer = null;
let shownNotificationIds = new Set();

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

function setVibeLock(locked) {
  vibeRequired = locked;
  document.body.classList.toggle("vibe-locked", locked);
  if (vibeBanner) vibeBanner.hidden = !locked;
  if (locked) {
    input.placeholder = "Tap an option below — or type A, B, C, or D";
    if (document.querySelector(".fineprint")) {
      document.querySelector(".fineprint").textContent =
        "Vibe check first · then order, pulse, and matches unlock";
    }
  } else {
    input.placeholder = "Craving, room pulse, or who to meet…";
    if (document.querySelector(".fineprint")) {
      document.querySelector(".fineprint").textContent =
        "Demo tickets · confirm real pricing at the counter";
    }
  }
}

function renderVibeOptions(question) {
  if (!question?.options?.length || !chipsEl) return;
  currentVibeQuestion = question;
  chipsEl.innerHTML = "";
  chipsEl.setAttribute("aria-label", question.prompt || "Vibe options");
  for (const opt of question.options) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "chip vibe-option";
    const key = opt.choice_key || "";
    btn.textContent = `${opt.emoji || ""} ${key ? `${key}. ` : ""}${opt.label}`.trim();
    btn.addEventListener("click", () => {
      submitVibeChoice(opt.id);
    });
    chipsEl.appendChild(btn);
  }
}

function presentVibeQuestion(question) {
  if (!question) return;
  const opts = (question.options || [])
    .map(
      (o) =>
        `**${o.choice_key}.** ${o.emoji || ""} ${o.label}`.replace(/\s+/g, " ").trim()
    )
    .join("\n");
  addMessage(
    "assistant",
    `**Vibe ${question.index}/${question.total}** — ${question.prompt}\n\n${opts}`
  );
  renderVibeOptions(question);
}

async function beginMandatoryVibe({ isNew = false, quiet = false } = {}) {
  setVibeLock(true);
  chipsEl.innerHTML = "";
  if (!quiet) {
    const hello = isNew
      ? "Welcome aboard — new guests start with a quick vibe check (takes ~20 seconds)."
      : "One more thing — finish your vibe check to unlock the café.";
    addMessage("assistant", hello);
  }

  try {
    const res = await fetch("/api/vibe/start", { method: "POST" });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || data.message || "Vibe start failed");
    if (data.phase === "complete" && data.personality) {
      finishVibeOnboarding(data.personality);
      return data;
    }
    if (data.question) presentVibeQuestion(data.question);
    return data;
  } catch (err) {
    addMessage(
      "assistant",
      `Couldn’t start vibe check: ${err.message}. Tap send once to retry.`
    );
    return null;
  }
}

function applyVibePayload(vibe) {
  if (!vibe) return;
  if (vibe.phase === "complete" && vibe.personality) {
    finishVibeOnboarding(vibe.personality);
    return;
  }
  if (vibe.question) presentVibeQuestion(vibe.question);
}

async function submitVibeChoice(choice) {
  if (busy) return;
  if (!currentVibeQuestion) {
    await beginMandatoryVibe({ quiet: true });
    if (!currentVibeQuestion) return;
  }
  const qid = currentVibeQuestion.id;
  const matched = currentVibeQuestion.options?.find(
    (o) =>
      o.id === choice ||
      o.label.toLowerCase() === String(choice).toLowerCase()
  );
  const payload = matched?.id || choice;
  const label = matched?.label || choice;

  busy = true;
  sendBtn.disabled = true;
  addMessage("user", label);
  input.value = "";
  autoGrow();
  const thinking = addMessage("assistant", "Reading your vibe…", { thinking: true });

  try {
    const res = await fetch("/api/vibe/answer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question_id: qid, choice: payload }),
    });
    const data = await res.json();
    thinking.row.remove();
    if (!res.ok) {
      const detail = data.detail || data.message || "Answer failed";
      // Invalid choice — re-show options instead of escalating to chat
      addMessage("assistant", `${detail}\n\nTap A–D below.`);
      if (currentVibeQuestion) renderVibeOptions(currentVibeQuestion);
      else await beginMandatoryVibe({ quiet: true });
      return;
    }

    if (data.phase === "complete" && data.personality) {
      finishVibeOnboarding(data.personality);
      return;
    }
    if (data.question) presentVibeQuestion(data.question);
  } catch (err) {
    thinking.row.remove();
    addMessage("assistant", `Hmm — ${err.message}. Tap an option again.`);
  } finally {
    busy = false;
    sendBtn.disabled = false;
    input.focus();
  }
}

function finishVibeOnboarding(personality) {
  updatePersonality(personality);
  setVibeLock(false);
  currentVibeQuestion = null;
  if (currentUser) {
    currentUser.personality = personality;
    currentUser.vibe_required = false;
  }
  renderChips();
  addMessage(
    "assistant",
    `Personality locked: **${personality.label}**.\n\n${personality.blurb}\n\n${personality.drink_hint}\n\nYou’re in — ask for a drink, the room pulse, or who matches your vibe (asli guests only).`
  );
  openSheet();
  refreshMatches();
  startNotifyPolling();
}

function renderMatches(matches) {
  if (!matchesListEl) return;
  if (!matches?.length) {
    matchesListEl.classList.add("empty");
    matchesListEl.innerHTML =
      "<p>Ask “Who matches my vibe?” — only real signed-in guests show up.</p>";
    refreshSheetBody();
    return;
  }
  matchesListEl.classList.remove("empty");
  matchesListEl.innerHTML = matches
    .map((m) => {
      const handle = escapeHtml(m.handle || "Guest");
      const vibe = escapeHtml(m.personality || "Café guest");
      const shared = escapeHtml((m.shared || []).slice(0, 3).join(", ") || "shared vibes");
      const sub = escapeHtml(m.matched_sub || m.sub || "");
      const notified = m.notified;
      const initial = escapeHtml((m.handle || "G").trim()[0] || "G").toUpperCase();
      const avatar = m.picture
        ? `<img src="${escapeHtml(m.picture)}" alt="" width="36" height="36" />`
        : `<span class="match-avatar">${initial}</span>`;
      return `
        <div class="match-row" data-sub="${sub}">
          ${avatar}
          <div class="match-meta">
            <p class="name">${handle}</p>
            <p class="sub">${vibe} · ${shared}</p>
          </div>
          <button type="button" class="match-notify" data-sub="${sub}" ${
            notified ? "disabled" : ""
          }>${notified ? "Notified" : "Notify"}</button>
        </div>`;
    })
    .join("");

  matchesListEl.querySelectorAll(".match-notify").forEach((btn) => {
    btn.addEventListener("click", () => notifyMatch(btn.dataset.sub, btn));
  });
  refreshSheetBody();
}

async function refreshMatches() {
  if (vibeRequired) return;
  try {
    const res = await fetch("/api/matches");
    if (!res.ok) return;
    const data = await res.json();
    renderMatches(data.matches || []);
  } catch {
    /* ignore */
  }
}

async function notifyMatch(matchedSub, btn) {
  if (!matchedSub) return;
  if (btn) {
    btn.disabled = true;
    btn.textContent = "Sending…";
  }
  try {
    const res = await fetch("/api/matches/notify", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ matched_sub: matchedSub }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || data.message || "Notify failed");
    if (btn) btn.textContent = "Notified";
    addMessage("assistant", data.message || "Notify bhej diya — unke screen pe popup aayega.");
    await refreshMatches();
  } catch (err) {
    if (btn) {
      btn.disabled = false;
      btn.textContent = "Notify";
    }
    addMessage("assistant", `Notify nahi gaya: ${err.message}`);
  }
}

function showMatchToast(message) {
  if (!matchToast || !matchToastMsg) return;
  matchToastMsg.textContent = message;
  matchToast.hidden = false;
}

function hideMatchToast() {
  if (matchToast) matchToast.hidden = true;
}

async function pollNotifications() {
  if (!currentUser || vibeRequired || document.hidden) return;
  try {
    const res = await fetch("/api/notifications");
    if (!res.ok) return;
    const data = await res.json();
    const notes = data.notifications || [];
    const fresh = notes.filter((n) => !shownNotificationIds.has(n.id));
    if (!fresh.length) return;
    const first = fresh[0];
    shownNotificationIds.add(first.id);
    showMatchToast(first.message);
    addMessage("assistant", `**Vibe ping!** ${first.message}`);
    await refreshMatches();
    await fetch("/api/notifications/read", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ids: fresh.map((n) => n.id) }),
    });
    fresh.forEach((n) => shownNotificationIds.add(n.id));
  } catch {
    /* ignore */
  }
}

function startNotifyPolling() {
  stopNotifyPolling();
  notifyPollTimer = setInterval(pollNotifications, 4000);
  pollNotifications();
}

function stopNotifyPolling() {
  if (notifyPollTimer) {
    clearInterval(notifyPollTimer);
    notifyPollTimer = null;
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
    if (
      (name === "find_connection" || name === "list_my_matches") &&
      response?.status === "success"
    ) {
      const list = response.matches || (response.match ? [response.match] : []);
      if (list.length) {
        renderMatches(
          list.map((m) => ({
            ...m,
            matched_sub: m.matched_sub || m.sub,
          }))
        );
      }
      refreshMatches();
    }
    if (name === "notify_match" && response?.status === "success") {
      refreshMatches();
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

function showApp(user, swiggy, { isNew = false, forceVibe = false } = {}) {
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

  const needsVibe = forceVibe || user.vibe_required || !user.personality;
  if (needsVibe) {
    if (!vibeBootstrapped) {
      vibeBootstrapped = true;
      messagesEl.innerHTML = "";
      beginMandatoryVibe({ isNew });
    }
  } else {
    setVibeLock(false);
    refreshMatches();
    startNotifyPolling();
    if (!messagesEl.childElementCount) {
      addMessage(
        "assistant",
        `Hi ${user.name || "there"} — welcome back to Café Concierge at Third Wave Kondapur.\n\nYou’re vibing as **${user.personality.label}** — ask who matches your vibe (real guests only), or Notify them from the matches panel.\n\nAvatar menu → **Connect Swiggy** for delivery discovery.`
      );
    }
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
    vibeBootstrapped = false;
    const me = await fetch("/api/me").then((r) => r.json());
    if (me.authenticated) {
      showApp(
        { ...me.user, recent_orders: me.recent_orders },
        me.swiggy,
        { isNew: Boolean(data.is_new), forceVibe: Boolean(data.vibe_required) }
      );
    } else {
      showApp(
        { ...data.user, recent_orders: [] },
        null,
        { isNew: Boolean(data.is_new), forceVibe: Boolean(data.vibe_required) }
      );
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
  const config = await fetch("/api/config").then((r) => r.json());
  if (!config.auth_configured) {
    showGate(
      "Add GOOGLE_CLIENT_ID to .env.local (Google Cloud → Credentials → OAuth client ID → Web). Origins must include http://localhost:5173."
    );
    return;
  }

  const me = await fetch("/api/me").then((r) => r.json());
  if (me.authenticated) {
    const needsVibe = Boolean(me.vibe_required || me.user?.vibe_required);
    if (!needsVibe) renderChips();
    showApp(
      { ...me.user, recent_orders: me.recent_orders },
      me.swiggy,
      { forceVibe: needsVibe }
    );
    if (!needsVibe) consumeSwiggyQuery();
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

  // Mandatory vibe: never hit /api/chat until personality is saved
  if (vibeRequired || currentUser?.vibe_required) {
    setVibeLock(true);
    if (!currentVibeQuestion) {
      await beginMandatoryVibe({ quiet: true });
      if (!currentVibeQuestion) return;
    }
    const letter = trimmed.toUpperCase();
    if (letter.length === 1 && "ABCD".includes(letter)) {
      const idx = letter.charCodeAt(0) - 65;
      const opt = currentVibeQuestion.options?.[idx];
      if (opt) {
        await submitVibeChoice(opt.id);
        return;
      }
    }
    const byLabel = currentVibeQuestion.options?.find(
      (o) =>
        o.label.toLowerCase() === trimmed.toLowerCase() ||
        o.id.toLowerCase() === trimmed.toLowerCase()
    );
    if (byLabel) {
      await submitVibeChoice(byLabel.id);
      return;
    }
    // Soft match: pass label text to answer endpoint
    await submitVibeChoice(trimmed);
    return;
  }

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

    // Server may still steer first-timers back into the vibe quiz
    if (data.vibe_required || data.vibe?.phase === "question") {
      setVibeLock(true);
      if (currentUser) currentUser.vibe_required = true;
      addMessage("assistant", data.reply || "Vibe check pehle.");
      applyVibePayload(data.vibe);
      return;
    }
    if (data.vibe?.phase === "complete" && data.vibe.personality) {
      finishVibeOnboarding(data.vibe.personality);
      return;
    }

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
  stopNotifyPolling();
  hideMatchToast();
  await fetch("/api/logout", { method: "POST" });
  messagesEl.innerHTML = "";
  currentUser = null;
  hasTicket = false;
  vibeBootstrapped = false;
  currentVibeQuestion = null;
  shownNotificationIds = new Set();
  setVibeLock(false);
  setSheetPeekState();
  showGate();
});

matchToastDismiss?.addEventListener("click", hideMatchToast);
matchToast?.addEventListener("click", (e) => {
  if (e.target === matchToast) hideMatchToast();
});

document.addEventListener("visibilitychange", () => {
  if (!document.hidden && currentUser && !vibeRequired) pollNotifications();
});

bootstrap();
