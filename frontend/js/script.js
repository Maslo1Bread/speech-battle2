/**
 * Speech-Battle — главная арена переговоров
 */

const LockIcon = `
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
    <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
    <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
  </svg>
`;

const state = {
  me: null,
  scenarios: [],
  scenarioId: null,
  difficulty: "easy",
  mode: "ai", // ai | human
  negotiationId: null,
  negotiation: null,
  searching: false,
  matchedHuman: false,
  ws: null,
  typingTimer: null,
  turnTimerInterval: null,
  aiStartedByButton: false,
};

document.addEventListener("DOMContentLoaded", async () => {
  if (!SB.requireAuth({ userOnly: true })) return;

  // Гарантированно скрыть «событийные» UI до реальных действий
  resetEventUi();
  setComposerEnabled(false);

  initNav();
  initDifficulty();
  initMode();
  initChat();
  initVoice();
  initFinish();

  try {
    state.me = await SB.api("/api/auth/me");
    await loadScenarios();
    connectWs();
    setComposerEnabled(true);
  } catch (err) {
    console.error(err);
    if (err.status === 401) SB.logout();
  }
});

/** Сброс поиска / печати / «Завершить» в исходное скрытое состояние */
function resetEventUi() {
  state.searching = false;
  state.matchedHuman = false;
  showSearchPanel(false);
  hideTyping();
  updateFinishVisibility();
  document.getElementById("scenarios-panel")?.classList.remove("is-hidden");
  const diffRow = document.getElementById("difficulty-row");
  if (diffRow) diffRow.hidden = false;
  document.getElementById("mode-section")?.classList.remove("is-dimmed");
  stopTurnTimer();
}

function setComposerEnabled(enabled) {
  const input = document.getElementById("chat-input");
  const send = document.getElementById("send-btn");
  const voice = document.getElementById("voice-btn");
  if (input) input.disabled = !enabled;
  if (send) send.disabled = !enabled;
  if (voice) voice.disabled = !enabled;
}

function initNav() {
  document.getElementById("logout-btn")?.addEventListener("click", () => SB.logout());
  const toggle = document.getElementById("nav-toggle");
  const links = document.getElementById("nav-links");
  toggle?.addEventListener("click", () => {
    const open = links.classList.toggle("is-open");
    toggle.setAttribute("aria-expanded", String(open));
  });
}

async function loadScenarios() {
  state.scenarios = await SB.api("/api/negotiations/scenarios");
  const list = document.getElementById("scenarios-list");
  const titleEl = document.getElementById("chat-scenario-title");
  const descEl = document.getElementById("chat-scenario-desc");

  list.innerHTML = state.scenarios
    .map((scenario, index) => {
      const lockedClass = scenario.locked ? " scenario-item--locked" : "";
      const lockMarkup = scenario.locked ? `<span class="scenario-item__lock">${LockIcon}</span>` : "";
      return `
        <li>
          <button type="button" class="scenario-item${lockedClass}" data-scenario-id="${scenario.id}"
            ${scenario.locked ? "disabled" : ""} aria-pressed="false">
            <span class="scenario-item__index">${index + 1}</span>
            <span class="scenario-item__body">
              <span class="scenario-item__name">${SB.escapeHtml(scenario.name)}</span>
              <span class="scenario-item__desc">${SB.escapeHtml(scenario.desc)}</span>
            </span>
            ${lockMarkup}
          </button>
        </li>`;
    })
    .join("");

  list.addEventListener("click", (event) => {
    if (state.matchedHuman || state.searching) return;
    const btn = event.target.closest(".scenario-item");
    if (!btn || btn.disabled) return;
    const scenario = state.scenarios.find((s) => s.id === btn.dataset.scenarioId);
    if (!scenario) return;

    list.querySelectorAll(".scenario-item").forEach((item) => {
      item.classList.remove("scenario-item--active");
      item.setAttribute("aria-pressed", "false");
    });
    btn.classList.add("scenario-item--active");
    btn.setAttribute("aria-pressed", "true");
    state.scenarioId = scenario.id;
    titleEl.textContent = scenario.name;
    descEl.textContent = scenario.desc;
    // новый сценарий — сбрасываем текущую AI-сессию
    if (!state.matchedHuman) {
      state.negotiationId = null;
      state.negotiation = null;
      state.aiStartedByButton = false;
      resetMessages();
    }
  });

  const first = list.querySelector(".scenario-item:not(:disabled)");
  first?.click();
}

function initDifficulty() {
  document.querySelectorAll("#difficulty-row .difficulty__btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      if (state.matchedHuman) return;
      document.querySelectorAll("#difficulty-row .difficulty__btn").forEach((b) => {
        b.classList.remove("difficulty__btn--active");
        b.setAttribute("aria-pressed", "false");
      });
      btn.classList.add("difficulty__btn--active");
      btn.setAttribute("aria-pressed", "true");
      state.difficulty = btn.dataset.difficulty;
      if (!state.matchedHuman) {
        state.negotiationId = null;
        state.aiStartedByButton = false;
      }
    });
  });
}

function initMode() {
  document.querySelectorAll(".type__btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      if (state.matchedHuman) return;

      const nextMode = btn.dataset.mode;

      if (nextMode === "human") {
        const started = await startHumanSearch();
        if (!started) {
          // вернуть подсветку на нейросеть
          document.querySelectorAll(".type__btn").forEach((b) => {
            const active = b.dataset.mode === "ai";
            b.classList.toggle("type__btn--active", active);
            b.setAttribute("aria-pressed", String(active));
          });
          state.mode = "ai";
          return;
        }
        document.querySelectorAll(".type__btn").forEach((b) => {
          b.classList.remove("type__btn--active");
          b.setAttribute("aria-pressed", "false");
        });
        btn.classList.add("type__btn--active");
        btn.setAttribute("aria-pressed", "true");
        state.mode = "human";
        return;
      }

      document.querySelectorAll(".type__btn").forEach((b) => {
        b.classList.remove("type__btn--active");
        b.setAttribute("aria-pressed", "false");
      });
      btn.classList.add("type__btn--active");
      btn.setAttribute("aria-pressed", "true");
      state.mode = "ai";

      // Режим нейросети: остановить поиск, не показывать search UI
      cancelHumanSearch();
      showSearchPanel(false);
      // Нейросеть начинает первой только по явному нажатию кнопки
      await startAiSession({ aiStarts: true });
    });
  });

  document.getElementById("cancel-search-btn")?.addEventListener("click", () => {
    cancelHumanSearch();
    showSearchPanel(false);
    // Вернуть UI на нейросеть без автостарта чата
    document.querySelectorAll(".type__btn").forEach((b) => {
      const active = b.dataset.mode === "ai";
      b.classList.toggle("type__btn--active", active);
      b.setAttribute("aria-pressed", String(active));
    });
    state.mode = "ai";
    setStatus("Готов к диалогу");
  });
}

function initFinish() {
  document.getElementById("finish-btn")?.addEventListener("click", async () => {
    if (!state.negotiationId) return;
    try {
      const neg = await SB.api(`/api/negotiations/${state.negotiationId}/finish`, { method: "POST" });
      applyNegotiation(neg, { redraw: true });
      setStatus("Отправлено на проверку");
      exitHumanMatchUi();
      updateFinishVisibility();
    } catch (err) {
      setHint(err.message);
    }
  });
}

/** Кнопка «Завершить» — только при активном чате с хотя бы одним неслужебным сообщением */
function updateFinishVisibility() {
  const row = document.getElementById("finish-row");
  if (!row) return;
  const msgs = state.negotiation?.messages || [];
  const hasContent = msgs.some(
    (m) => m.sender_type === "user" || m.sender_type === "ai",
  );
  const active = Boolean(
    state.negotiationId && state.negotiation?.status === "active" && hasContent,
  );
  row.hidden = !active;
  row.classList.toggle("is-hidden", !active);
}

function setStatus(text) {
  const el = document.getElementById("chat-status-text");
  if (el) el.textContent = text;
}

function setHint(text) {
  const hint = document.getElementById("voice-hint");
  if (!hint) return;
  hint.hidden = !text;
  hint.textContent = text || "";
}

function resetMessages() {
  const box = document.getElementById("chat-messages");
  box.innerHTML = `
    <div class="chat-empty" id="chat-empty">
      <div class="chat-empty__icon" aria-hidden="true">
        <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="1.8">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
      </div>
      Выберите режим и сценарий. Можно писать или диктовать сообщение.
    </div>`;
  hideTyping();
  stopTurnTimer();
  updateFinishVisibility();
}

function clearEmpty() {
  document.getElementById("chat-empty")?.remove();
}

function appendMessage({ content, mine = false, system = false, warning = false, bot = false, animate = false, createdAt = null }) {
  clearEmpty();
  const box = document.getElementById("chat-messages");
  const msg = document.createElement("div");
  msg.className = warning
    ? "chat-msg chat-msg--system chat-msg--warning"
    : system
      ? "chat-msg chat-msg--system"
      : mine
        ? "chat-msg chat-msg--user"
        : "chat-msg chat-msg--bot";

  const meta = document.createElement("span");
  meta.className = "chat-msg__meta";
  meta.textContent = SB.formatTime(createdAt || new Date());

  if (animate && !mine && !system) {
    msg.textContent = "";
    box.appendChild(msg);
    box.scrollTop = box.scrollHeight;
    typeInto(msg, content).then(() => {
      msg.appendChild(meta);
      box.scrollTop = box.scrollHeight;
    });
  } else {
    msg.textContent = content;
    msg.appendChild(meta);
    box.appendChild(msg);
    box.scrollTop = box.scrollHeight;
  }
}

function typeInto(el, text) {
  return new Promise((resolve) => {
    let i = 0;
    const step = () => {
      el.textContent = text.slice(0, i);
      i += 1;
      const box = document.getElementById("chat-messages");
      box.scrollTop = box.scrollHeight;
      if (i <= text.length) setTimeout(step, 16 + Math.random() * 22);
      else resolve();
    };
    step();
  });
}

function showTyping(label = "Собеседник печатает…") {
  const el = document.getElementById("typing-indicator");
  const lab = document.getElementById("typing-label");
  if (lab) lab.textContent = label;
  if (el) {
    el.hidden = false;
    el.classList.add("is-visible");
  }
}

function hideTyping() {
  const el = document.getElementById("typing-indicator");
  if (el) {
    el.hidden = true;
    el.classList.remove("is-visible");
  }
}

async function ensureAiSession() {
  if (
    state.negotiationId &&
    state.negotiation?.mode === "ai" &&
    state.negotiation?.status === "active"
  ) {
    return state.negotiationId;
  }
  return startAiSession({ aiStarts: false });
}

async function startAiSession({ aiStarts }) {
  if (!state.scenarioId) {
    setHint("Сначала выберите сценарий");
    return null;
  }
  setStatus(aiStarts ? "Нейросеть начинает…" : "Диалог с нейросетью");
  // Индикатор печати — только когда ИИ реально генерирует ответ
  if (aiStarts) showTyping("Нейросеть печатает…");
  try {
    const neg = await SB.api("/api/negotiations/ai/start", {
      method: "POST",
      body: JSON.stringify({
        scenario_id: state.scenarioId,
        difficulty: state.difficulty,
        ai_starts: aiStarts,
      }),
    });
    state.mode = "ai";
    state.aiStartedByButton = aiStarts;
    applyNegotiation(neg, {
      animateLastBot: aiStarts,
      redraw: aiStarts || Boolean(neg.messages?.length),
    });
    hideTyping();
    setStatus("Диалог с нейросетью");
    updateFinishVisibility();
    return neg.id;
  } catch (err) {
    hideTyping();
    setHint(err.message);
    return null;
  }
}

function applyNegotiation(neg, { animateLastBot = false, redraw = true } = {}) {
  state.negotiation = neg;
  state.negotiationId = neg.id;
  if (redraw) {
    const box = document.getElementById("chat-messages");
    box.innerHTML = "";
    if (!neg.messages?.length) {
      resetMessages();
    } else {
      neg.messages.forEach((m, idx) => {
        const isLast = idx === neg.messages.length - 1;
        appendMessage({
          content: m.content,
          mine: m.is_mine,
          system: m.sender_type === "system",
          bot: m.sender_type === "ai" || (!m.is_mine && m.sender_type === "user"),
          animate: animateLastBot && isLast && m.sender_type === "ai",
          createdAt: m.created_at,
        });
      });
    }
  }
  if (neg.mode === "human" && neg.status === "active") {
    enterHumanMatchUi(neg);
    updateTurnTimer(neg);
  }
  if (neg.status === "pending_review" || neg.status === "reviewed") {
    stopTurnTimer();
  }
  updateFinishVisibility();
}

function restoreChatAfterFailedSend(text, err) {
  const input = document.getElementById("chat-input");
  if (state.negotiation?.messages?.length) {
    applyNegotiation(state.negotiation, { redraw: true });
  } else {
    resetMessages();
  }
  if (input) input.value = text;
  const message = err?.message || "Не удалось отправить сообщение";
  setHint(message);
  if (err?.code === "off_topic") {
    appendMessage({ content: message, warning: true });
  }
}

function initChat() {
  const form = document.getElementById("chat-form");
  const input = document.getElementById("chat-input");
  let sending = false;

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (sending) return;

    const text = input.value.trim();
    if (!text) return;

    if (!state.scenarioId) {
      setHint("Сначала выберите сценарий");
      return;
    }

    if (state.searching || (state.mode === "human" && !state.matchedHuman)) {
      setHint("Дождитесь оппонента или отмените поиск");
      return;
    }

    if (state.mode === "human" && !state.negotiationId) {
      setHint("Нет активного чата с оппонентом");
      return;
    }

    sending = true;
    setComposerEnabled(false);
    input.value = "";
    setHint("");
    appendMessage({ content: text, mine: true });

    try {
      if (state.mode !== "human") {
        const id = await ensureAiSession();
        if (!id) {
          restoreChatAfterFailedSend(text, { message: "Не удалось начать диалог с нейросетью" });
          return;
        }
        showTyping("Нейросеть печатает…");
        const neg = await SB.api(`/api/negotiations/${id}/messages`, {
          method: "POST",
          body: JSON.stringify({ content: text }),
        });
        hideTyping();
        // Полная перерисовка с анимацией последнего ответа ИИ
        applyNegotiation(neg, { animateLastBot: true, redraw: true });
        setStatus("Диалог с нейросетью");
      } else {
        sendTyping(false);
        const neg = await SB.api(`/api/negotiations/${state.negotiationId}/messages`, {
          method: "POST",
          body: JSON.stringify({ content: text }),
        });
        state.negotiation = neg;
        updateTurnTimer(neg);
        updateFinishVisibility();
      }
    } catch (err) {
      hideTyping();
      restoreChatAfterFailedSend(text, err);
    } finally {
      sending = false;
      setComposerEnabled(true);
      input.focus();
    }
  });

  let typingSendTimer;
  input.addEventListener("input", () => {
    if (!state.matchedHuman || !state.negotiationId || !state.ws) return;
    sendTyping(true);
    clearTimeout(typingSendTimer);
    typingSendTimer = setTimeout(() => sendTyping(false), 1200);
  });
}

function sendTyping(isTyping) {
  if (!state.ws || state.ws.readyState !== WebSocket.OPEN || !state.negotiationId) return;
  state.ws.send(
    JSON.stringify({
      action: "typing",
      negotiation_id: state.negotiationId,
      is_typing: isTyping,
    }),
  );
}

function connectWs() {
  const ws = new WebSocket(SB.wsUrl());
  state.ws = ws;

  ws.addEventListener("open", () => {
    ws.send(JSON.stringify({ type: "auth", token: SB.token }));
  });

  ws.addEventListener("message", async (event) => {
    let data;
    try {
      data = JSON.parse(event.data);
    } catch {
      return;
    }

    if (data.type === "ready") {
      // Сокет готов — UI поиска не трогаем, пока нет action=search
      return;
    }

    if (data.type === "searching") {
      state.searching = true;
      state.mode = "human";
      showSearchPanel(true);
      setStatus("Поиск оппонента…");
    }

    if (data.type === "search_cancelled") {
      state.searching = false;
      showSearchPanel(false);
      setStatus("Поиск отменён");
    }

    if (data.type === "matched") {
      state.searching = false;
      state.matchedHuman = true;
      state.mode = "human";
      state.negotiationId = data.negotiation_id;
      state.negotiation = {
        id: data.negotiation_id,
        mode: "human",
        status: "active",
        messages: [],
        current_turn_user_id: data.current_turn_user_id,
        turn_deadline: data.turn_deadline,
      };
      showSearchPanel(false);
      hideTyping();
      enterHumanMatchUi(data);
      setStatus("Оппонент найден");
      resetMessages();
      if (data.system_message) {
        appendMessage({ content: data.system_message, system: true });
        state.negotiation.messages = [
          { sender_type: "system", content: data.system_message },
        ];
      }
      updateFinishVisibility();
      ws.send(JSON.stringify({ action: "join_room", negotiation_id: data.negotiation_id }));
      updateTurnTimer({
        current_turn_user_id: data.current_turn_user_id,
        turn_deadline: data.turn_deadline,
        status: "active",
        mode: "human",
      });
    }

    if (data.type === "message" && data.negotiation_id === state.negotiationId) {
      const mine = data.message.sender_id === state.me.id;
      if (!mine) {
        hideTyping();
        appendMessage({
          content: data.message.content,
          mine: false,
          animate: true,
          createdAt: data.message.created_at,
        });
      }
      if (state.negotiation) {
        state.negotiation.messages = state.negotiation.messages || [];
        const already = state.negotiation.messages.some(
          (m) =>
            (data.message.id && m.id === data.message.id) ||
            (m.content === data.message.content && m.sender_id === data.message.sender_id),
        );
        if (!already) {
          state.negotiation.messages.push({
            id: data.message.id,
            sender_type: "user",
            sender_id: data.message.sender_id,
            content: data.message.content,
          });
        }
        state.negotiation.status = "active";
      }
      updateFinishVisibility();
      updateTurnTimer({
        current_turn_user_id: data.current_turn_user_id,
        turn_deadline: data.turn_deadline,
        status: "active",
        mode: "human",
      });
    }

    if (data.type === "typing" && data.negotiation_id === state.negotiationId) {
      if (data.user_id !== state.me.id) {
        if (data.is_typing) showTyping("Оппонент печатает…");
        else hideTyping();
      }
    }

    if (data.type === "finished" && data.negotiation_id === state.negotiationId) {
      hideTyping();
      appendMessage({
        content:
          data.reason === "timeout"
            ? "Время хода истекло. Чат отправлен на проверку."
            : "Переговоры завершены и отправлены на проверку.",
        system: true,
      });
      setStatus("На проверке");
      exitHumanMatchUi();
      stopTurnTimer();
    }

    if (data.type === "error") {
      setHint(data.detail || "Ошибка соединения");
    }
  });

  ws.addEventListener("close", () => {
    setTimeout(connectWs, 2000);
  });
}

async function startHumanSearch() {
  if (!state.scenarioId) {
    setHint("Сначала выберите сценарий");
    return false;
  }
  if (!state.ws || state.ws.readyState !== WebSocket.OPEN) {
    setHint("Соединение ещё устанавливается, подождите секунду…");
    return false;
  }
  state.searching = true;
  state.mode = "human";
  showSearchPanel(true);
  setStatus("Поиск оппонента…");
  state.ws.send(
    JSON.stringify({
      action: "search",
      scenario_id: state.scenarioId,
      difficulty: state.difficulty,
    }),
  );
  return true;
}

function cancelHumanSearch() {
  state.searching = false;
  showSearchPanel(false);
  if (state.ws && state.ws.readyState === WebSocket.OPEN) {
    state.ws.send(JSON.stringify({ action: "cancel_search" }));
  }
}

function showSearchPanel(show) {
  const panel = document.getElementById("search-panel");
  if (!panel) return;
  panel.hidden = !show;
  panel.classList.toggle("is-visible", Boolean(show));
}

function enterHumanMatchUi(negOrData) {
  state.matchedHuman = true;
  document.getElementById("scenarios-panel")?.classList.add("is-hidden");
  const diffRow = document.getElementById("difficulty-row");
  if (diffRow) diffRow.hidden = true;
  document.getElementById("mode-section")?.classList.add("is-dimmed");
  const title = document.getElementById("chat-scenario-title");
  const desc = document.getElementById("chat-scenario-desc");
  if (negOrData.scenario_title && title) title.textContent = negOrData.scenario_title;
  if (desc) desc.textContent = "Переговоры с реальным оппонентом";
  // «Завершить» только после появления сообщений пользователя/ИИ
  updateFinishVisibility();
}

function exitHumanMatchUi() {
  state.matchedHuman = false;
  state.searching = false;
  document.getElementById("scenarios-panel")?.classList.remove("is-hidden");
  const diffRow = document.getElementById("difficulty-row");
  if (diffRow) diffRow.hidden = false;
  document.getElementById("mode-section")?.classList.remove("is-dimmed");
  showSearchPanel(false);
  hideTyping();
  updateFinishVisibility();
}

function updateTurnTimer(neg) {
  stopTurnTimer();
  const el = document.getElementById("turn-timer");
  if (!neg || neg.mode !== "human" || neg.status !== "active" || !neg.turn_deadline) {
    if (el) el.hidden = true;
    return;
  }
  el.hidden = false;
  const myTurn = neg.current_turn_user_id === state.me?.id;

  const tick = async () => {
    const deadline = new Date(neg.turn_deadline).getTime();
    const left = Math.max(0, deadline - Date.now());
    const sec = Math.ceil(left / 1000);
    const mm = String(Math.floor(sec / 60)).padStart(2, "0");
    const ss = String(sec % 60).padStart(2, "0");
    el.textContent = myTurn
      ? `Ваш ход: ${mm}:${ss}`
      : `Ход оппонента: ${mm}:${ss}`;
    if (left <= 0) {
      stopTurnTimer();
      try {
        const updated = await SB.api(`/api/negotiations/${state.negotiationId}/check-timeout`, {
          method: "POST",
        });
        if (updated.status !== "active") {
          appendMessage({
            content: "Время хода истекло. Чат отправлен на проверку.",
            system: true,
          });
          setStatus("На проверке");
          exitHumanMatchUi();
        }
      } catch (err) {
        console.error(err);
      }
    }
  };
  tick();
  state.turnTimerInterval = setInterval(tick, 500);
}

function stopTurnTimer() {
  if (state.turnTimerInterval) {
    clearInterval(state.turnTimerInterval);
    state.turnTimerInterval = null;
  }
  const el = document.getElementById("turn-timer");
  if (el) el.hidden = true;
}

/* ---------- Голосовой ввод (Chrome Speech API + Firefox Whisper fallback) ---------- */

function initVoice() {
  const voiceBtn = document.getElementById("voice-btn");
  const input = document.getElementById("chat-input");
  const hint = document.getElementById("voice-hint");
  if (!voiceBtn || !input) return;

  const ui = {
    setListening(active) {
      voiceBtn.classList.toggle("chat-composer__mic--active", active);
      voiceBtn.setAttribute("aria-pressed", String(active));
    },
    show(text) {
      if (!hint) return;
      hint.hidden = !text;
      hint.textContent = text || "";
    },
    clear() {
      this.show("");
    },
  };

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (SpeechRecognition) {
    initNativeVoice(SpeechRecognition, voiceBtn, input, ui);
    return;
  }
  if (navigator.mediaDevices?.getUserMedia && window.MediaRecorder) {
    initFirefoxVoice(voiceBtn, input, ui);
    return;
  }
  voiceBtn.disabled = true;
  ui.show("Голосовой ввод недоступен в этом браузере.");
}

function initNativeVoice(SpeechRecognition, voiceBtn, input, ui) {
  const recognition = new SpeechRecognition();
  recognition.lang = "ru-RU";
  recognition.interimResults = true;
  recognition.continuous = false;
  let listening = false;
  let finalTranscript = "";

  voiceBtn.addEventListener("click", () => {
    if (listening) {
      recognition.stop();
      return;
    }
    finalTranscript = input.value.trim() ? `${input.value.trim()} ` : "";
    try {
      recognition.start();
    } catch {
      /* ignore */
    }
  });

  recognition.addEventListener("start", () => {
    listening = true;
    ui.setListening(true);
    ui.show("Слушаю… говорите");
  });
  recognition.addEventListener("result", (event) => {
    let interim = "";
    for (let i = event.resultIndex; i < event.results.length; i += 1) {
      const chunk = event.results[i][0].transcript;
      if (event.results[i].isFinal) finalTranscript += chunk;
      else interim += chunk;
    }
    input.value = (finalTranscript + interim).trimStart();
  });
  recognition.addEventListener("error", (event) => {
    listening = false;
    ui.setListening(false);
    if (event.error !== "aborted") {
      ui.show("Ошибка голосового ввода. Проверьте микрофон.");
    }
  });
  recognition.addEventListener("end", () => {
    listening = false;
    ui.setListening(false);
    ui.clear();
  });
}

function initFirefoxVoice(voiceBtn, input, ui) {
  let mediaRecorder = null;
  let mediaStream = null;
  let chunks = [];
  let recording = false;
  let busy = false;
  let transcriberPromise = null;

  const stopTracks = () => {
    mediaStream?.getTracks().forEach((t) => t.stop());
    mediaStream = null;
  };

  const getTranscriber = async () => {
    if (!transcriberPromise) {
      ui.show("Загрузка модели распознавания…");
      transcriberPromise = import("https://cdn.jsdelivr.net/npm/@xenova/transformers@2.17.2").then(
        async (transformers) => {
          transformers.env.allowLocalModels = false;
          return transformers.pipeline("automatic-speech-recognition", "Xenova/whisper-tiny", {
            quantized: true,
          });
        },
      );
    }
    return transcriberPromise;
  };

  const processRecording = async (blob) => {
    busy = true;
    voiceBtn.disabled = true;
    ui.setListening(false);
    ui.show("Распознаю речь…");
    try {
      if (blob.size < 800) {
        ui.show("Слишком короткая запись");
        return;
      }
      const audioData = await decodeAudioTo16kMono(blob);
      const transcriber = await getTranscriber();
      const result = await transcriber(audioData, { language: "russian", task: "transcribe" });
      const text = (result?.text || "").trim();
      if (!text) {
        ui.show("Речь не распознана");
        return;
      }
      input.value = input.value.trim() ? `${input.value.trim()} ${text}` : text;
      ui.clear();
    } catch (error) {
      console.error(error);
      ui.show("Не удалось распознать речь");
    } finally {
      busy = false;
      voiceBtn.disabled = false;
    }
  };

  voiceBtn.addEventListener("click", async () => {
    if (busy) return;
    if (recording) {
      recording = false;
      mediaRecorder?.stop();
      return;
    }
    try {
      mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      chunks = [];
      const mime = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : "";
      mediaRecorder = mime ? new MediaRecorder(mediaStream, { mimeType: mime }) : new MediaRecorder(mediaStream);
      mediaRecorder.addEventListener("dataavailable", (e) => {
        if (e.data?.size) chunks.push(e.data);
      });
      mediaRecorder.addEventListener("stop", () => {
        const blob = new Blob(chunks, { type: mediaRecorder.mimeType || "audio/webm" });
        stopTracks();
        void processRecording(blob);
      });
      mediaRecorder.start();
      recording = true;
      ui.setListening(true);
      ui.show("Запись… нажмите микрофон ещё раз");
    } catch {
      ui.show("Нет доступа к микрофону");
      stopTracks();
    }
  });
}

async function decodeAudioTo16kMono(blob) {
  const arrayBuffer = await blob.arrayBuffer();
  const audioCtx = new AudioContext();
  let audioBuffer;
  try {
    audioBuffer = await audioCtx.decodeAudioData(arrayBuffer.slice(0));
  } finally {
    await audioCtx.close();
  }
  const length = audioBuffer.length;
  const mono = new Float32Array(length);
  for (let ch = 0; ch < audioBuffer.numberOfChannels; ch += 1) {
    const data = audioBuffer.getChannelData(ch);
    for (let i = 0; i < length; i += 1) mono[i] += data[i] / audioBuffer.numberOfChannels;
  }
  if (audioBuffer.sampleRate === 16000) return mono;
  const ratio = audioBuffer.sampleRate / 16000;
  const outLen = Math.max(1, Math.round(mono.length / ratio));
  const out = new Float32Array(outLen);
  for (let i = 0; i < outLen; i += 1) {
    const src = i * ratio;
    const idx = Math.floor(src);
    const frac = src - idx;
    const s0 = mono[idx] ?? 0;
    const s1 = mono[idx + 1] ?? s0;
    out[i] = s0 + (s1 - s0) * frac;
  }
  return out;
}
