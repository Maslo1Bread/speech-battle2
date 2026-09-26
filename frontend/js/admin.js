if (!SB.requireAuth({ adminOnly: true })) {
  /* redirect */
}

document.getElementById("logout-btn")?.addEventListener("click", () => SB.logout());
document.getElementById("nav-toggle")?.addEventListener("click", () => {
  document.getElementById("nav-links")?.classList.toggle("is-open");
});

const statusLabels = {
  pending_review: "Ждёт оценки",
  reviewed: "Оценено",
  active: "Активен",
};

function messageClass(m, participant1Id, participant2Id) {
  if (m.sender_type === "system") return "chat-msg chat-msg--system";
  if (m.sender_type === "ai") return "chat-msg chat-msg--bot";
  const twoHumans = Boolean(participant1Id && participant2Id);
  if (twoHumans) {
    return m.sender_id === participant1Id ? "chat-msg chat-msg--peer-a" : "chat-msg chat-msg--peer-b";
  }
  return "chat-msg chat-msg--user";
}

function renderMessages(messages, participant1Id, participant2Id) {
  return (messages || [])
    .map((m) => {
      const cls = messageClass(m, participant1Id, participant2Id);
      const label = m.sender_label || (m.sender_type === "ai" ? "Нейросеть" : m.sender_type === "system" ? "Система" : "Участник");
      const author =
        m.sender_type === "system"
          ? ""
          : `<span class="chat-msg__author">${SB.escapeHtml(label)}</span>`;
      return `<div class="${cls}">${author}${SB.escapeHtml(m.content)}
        <span class="chat-msg__meta">${SB.formatTime(m.created_at)}</span></div>`;
    })
    .join("");
}

function scoreFieldsHtml(participants, fallbackScore = 70) {
  const list = participants && participants.length ? participants : [{ id: 0, username: "участник", score: fallbackScore }];
  return list
    .map(
      (p) => `
      <label class="sb-field">
        <span>Оценка для @${SB.escapeHtml(p.username)} (1–100)</span>
        <input class="sb-input" type="number" name="score_${p.id}" min="1" max="100"
          value="${p.score != null ? p.score : fallbackScore}" required data-user-id="${p.id}">
      </label>`,
    )
    .join("");
}

function scoresPayloadFromForm(form, participants) {
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
}

function formatListScores(item) {
  const parts = item.participant_scores || [];
  if (parts.length > 1) {
    return parts
      .map((p) => (p.score != null ? `@${p.username}: ${p.score}` : `@${p.username}: —`))
      .join(" · ");
  }
  if (item.score != null) return `${item.score}/100`;
  return "";
}

async function loadReviews() {
  const list = document.getElementById("review-list");
  const items = await SB.api("/api/admin/reviews");
  if (!items.length) {
    list.innerHTML = `<li class="history-empty">Нет чатов на проверку</li>`;
    return;
  }
  list.innerHTML = items
    .map(
      (item) => `
      <li>
        <button type="button" class="history-item" data-id="${item.id}">
          <span class="history-item__title">${SB.escapeHtml(item.scenario_title)}</span>
          <span class="history-item__meta">
            ${item.mode === "ai" ? `Нейросеть · ${item.difficulty}` : "Человек"}
            · ${statusLabels[item.status] || item.status}
            ${formatListScores(item) ? `· ${SB.escapeHtml(formatListScores(item))}` : ""}
          </span>
          <span class="history-item__date">${SB.formatDate(item.created_at)}</span>
        </button>
      </li>`,
    )
    .join("");

  list.onclick = async (event) => {
    const btn = event.target.closest(".history-item");
    if (!btn) return;
    list.querySelectorAll(".history-item").forEach((el) => el.classList.remove("is-active"));
    btn.classList.add("is-active");
    await openReview(Number(btn.dataset.id));
  };
}

async function openReview(id) {
  const detail = document.getElementById("review-detail");
  const neg = await SB.api(`/api/admin/reviews/${id}`);
  const participants = neg.participants || [];
  const who =
    participants.length > 0
      ? participants.map((p) => `@${p.username}`).join(" и ")
      : "участники";

  detail.innerHTML = `
    <header class="chat-panel__header">
      <div>
        <h2 class="chat-panel__title">${SB.escapeHtml(neg.scenario_title)}</h2>
        <p class="chat-panel__subtitle">
          Тип: ${neg.mode === "ai" ? `нейросеть (${neg.difficulty})` : "реальный пользователь"}
          · ${SB.escapeHtml(who)}
        </p>
      </div>
    </header>
    <div class="chat-messages history-messages">
      ${renderMessages(neg.messages, neg.participant1_id, neg.participant2_id)}
    </div>
    <form class="score-form" id="score-form">
      ${scoreFieldsHtml(participants, neg.score || 70)}
      <button class="sb-btn sb-btn--primary" type="submit">Сохранить оценку</button>
      <p class="form-error" id="score-error" hidden></p>
      <p class="form-ok" id="score-ok" hidden>Оценка сохранена</p>
    </form>
  `;

  document.getElementById("score-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const error = document.getElementById("score-error");
    const ok = document.getElementById("score-ok");
    error.hidden = true;
    ok.hidden = true;
    try {
      await SB.api(`/api/admin/reviews/${id}/score`, {
        method: "POST",
        body: JSON.stringify(scoresPayloadFromForm(event.target, participants)),
      });
      ok.hidden = false;
      await loadReviews();
      await openReview(id);
    } catch (err) {
      error.hidden = false;
      error.textContent = err.message;
    }
  });
}

loadReviews().catch((err) => {
  if (err.status === 401 || err.status === 403) SB.logout();
});
