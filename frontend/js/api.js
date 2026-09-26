/**
 * Общий клиент API + авторизация.
 * Работает одинаково в Chrome / Firefox / Safari.
 */
const SB_TOKEN_KEY = "sb_token";
const SB_ROLE_KEY = "sb_role";

const SB = {
  get token() {
    return localStorage.getItem(SB_TOKEN_KEY);
  },
  get role() {
    return localStorage.getItem(SB_ROLE_KEY);
  },
  setSession(token, role) {
    localStorage.setItem(SB_TOKEN_KEY, token);
    localStorage.setItem(SB_ROLE_KEY, role);
  },
  clearSession() {
    localStorage.removeItem(SB_TOKEN_KEY);
    localStorage.removeItem(SB_ROLE_KEY);
  },
  isAuthed() {
    return Boolean(this.token);
  },
  wsUrl() {
    const proto = location.protocol === "https:" ? "wss:" : "ws:";
    return `${proto}//${location.host}/ws`;
  },
  async api(path, options = {}) {
    const headers = Object.assign(
      { "Content-Type": "application/json" },
      options.headers || {},
    );
    if (this.token) headers.Authorization = `Bearer ${this.token}`;

    const resp = await fetch(path, { ...options, headers });
    let data = null;
    const text = await resp.text();
    try {
      data = text ? JSON.parse(text) : null;
    } catch {
      data = { detail: text };
    }

    if (!resp.ok) {
      const detail = data?.detail;
      let message;
      let code;
      if (Array.isArray(detail)) {
        message = detail.map((d) => d.msg || JSON.stringify(d)).join("; ");
      } else if (detail && typeof detail === "object") {
        message = detail.message || detail.detail || JSON.stringify(detail);
        code = detail.code;
      } else {
        message = detail || `Ошибка ${resp.status}`;
      }
      const err = new Error(message);
      err.status = resp.status;
      err.code = code;
      err.data = data;
      throw err;
    }
    return data;
  },
  requireAuth({ adminOnly = false, userOnly = false } = {}) {
    if (!this.isAuthed()) {
      location.replace("/auth.html");
      return false;
    }
    if (adminOnly && this.role !== "admin") {
      location.replace("/index.html");
      return false;
    }
    if (userOnly && this.role === "admin") {
      location.replace("/admin.html");
      return false;
    }
    return true;
  },
  logout() {
    this.clearSession();
    location.replace("/auth.html");
  },
  escapeHtml(text) {
    return String(text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  },
  formatTime(value) {
    const date = value instanceof Date ? value : new Date(value);
    return date.toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" });
  },
  formatDate(value) {
    const date = value instanceof Date ? value : new Date(value);
    return date.toLocaleString("ru-RU", {
      day: "2-digit",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    });
  },
  animateNumber(el, to, { duration = 1200, suffix = "" } = {}) {
    if (!el) return;
    const start = performance.now();
    const from = 0;
    const tick = (now) => {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      const value = Math.round(from + (to - from) * eased);
      el.textContent = `${value}${suffix}`;
      if (t < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  },
  typeText(el, text, { speed = 28 } = {}) {
    if (!el) return Promise.resolve();
    el.textContent = "";
    return new Promise((resolve) => {
      let i = 0;
      const step = () => {
        el.textContent = text.slice(0, i);
        i += 1;
        if (i <= text.length) setTimeout(step, speed);
        else resolve();
      };
      step();
    });
  },
  messageAuthor(m) {
    if (m.sender_type === "system") return "";
    if (m.sender_type === "ai") return m.sender_label || "Нейросеть";
    const raw = m.sender_label || "Участник";
    return raw.startsWith("@") ? raw : `@${raw}`;
  },
  messageBubbleClass(m, participants) {
    if (m.sender_type === "system") return "chat-msg chat-msg--system";
    if (m.sender_type === "ai") return "chat-msg chat-msg--bot";
    const ids = (participants || []).map((p) => p.id).filter(Boolean);
    if (ids.length > 1 && m.sender_id === ids[1]) {
      return "chat-msg chat-msg--user chat-msg--p2";
    }
    return "chat-msg chat-msg--bot chat-msg--p1";
  },
  renderTranscript(messages, participants) {
    return (messages || [])
      .map((m) => {
        const author = this.messageAuthor(m);
        const authorHtml = author
          ? `<span class="chat-msg__author">${this.escapeHtml(author)}</span>`
          : "";
        return `<div class="${this.messageBubbleClass(m, participants)}">
          ${authorHtml}
          <span class="chat-msg__body">${this.escapeHtml(m.content)}</span>
          <span class="chat-msg__meta">${this.formatTime(m.created_at)}</span>
        </div>`;
      })
      .join("");
  },
  scoringParticipants(neg) {
    if (neg?.participants?.length) return neg.participants;
    const ids = [neg?.participant1_id, neg?.participant2_id].filter(Boolean);
    return ids.map((id) => ({
      id,
      username: `user#${id}`,
      full_name: "",
      score: neg?.score ?? null,
    }));
  },
  scoreFieldsHtml(participants, fallbackScore = 70) {
    const list =
      participants && participants.length
        ? participants
        : [{ id: 0, username: "участник", score: fallbackScore }];
    const cards = list
      .map(
        (p) => `
      <label class="score-card">
        <span class="score-card__name">@${this.escapeHtml(p.username)}</span>
        <span class="score-card__hint">Оценка 1–100</span>
        <input class="sb-input" type="number" name="score_${p.id}" min="1" max="100"
          value="${p.score != null ? p.score : fallbackScore}" required data-user-id="${p.id}">
      </label>`,
      )
      .join("");
    return `<div class="score-form__row">${cards}</div>`;
  },
  scoresPayloadFromForm(form, participants) {
    if (!participants?.length) {
      return { score: Number(form.querySelector('[name^="score_"]').value) };
    }
    if (participants.length === 1) {
      return { score: Number(form.querySelector(`[name="score_${participants[0].id}"]`).value) };
    }
    return {
      scores: participants.map((p) => ({
        user_id: p.id,
        score: Number(form.querySelector(`[name="score_${p.id}"]`).value),
      })),
    };
  },
  formatListScores(item) {
    const parts = item.participant_scores || [];
    if (parts.length > 1) {
      return parts
        .map((p) => (p.score != null ? `@${p.username}: ${p.score}` : `@${p.username}: —`))
        .join(" · ");
    }
    if (item.score != null) return `${item.score}/100`;
    return "";
  },
};

window.SB = SB;
