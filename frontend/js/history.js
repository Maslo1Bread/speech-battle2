if (!SB.requireAuth({ userOnly: true })) {
  /* redirect */
}

document.getElementById("logout-btn")?.addEventListener("click", () => SB.logout());
document.getElementById("nav-toggle")?.addEventListener("click", () => {
  document.getElementById("nav-links")?.classList.toggle("is-open");
});

const statusLabels = {
  active: "В процессе",
  pending_review: "На проверке",
  reviewed: "Оценено",
  cancelled: "Отменено",
};

async function loadHistory() {
  const list = document.getElementById("history-list");
  const items = await SB.api("/api/negotiations/history");
  if (!items.length) {
    list.innerHTML = `<li class="history-empty">Пока нет переговоров</li>`;
    return;
  }
  list.innerHTML = items
    .map(
      (item) => `
      <li>
        <button type="button" class="history-item" data-id="${item.id}">
          <span class="history-item__title">${SB.escapeHtml(item.scenario_title)}</span>
          <span class="history-item__meta">
            ${item.mode === "ai" ? "Нейросеть" : "Человек"}
            · ${item.difficulty}
            · ${statusLabels[item.status] || item.status}
            ${item.score != null ? `· ${item.score}/100` : ""}
          </span>
          <span class="history-item__date">${SB.formatDate(item.created_at)}</span>
        </button>
      </li>
    `,
    )
    .join("");

  list.addEventListener("click", async (event) => {
    const btn = event.target.closest(".history-item");
    if (!btn) return;
    list.querySelectorAll(".history-item").forEach((el) => el.classList.remove("is-active"));
    btn.classList.add("is-active");
    await openChat(Number(btn.dataset.id));
  });
}

async function openChat(id) {
  const detail = document.getElementById("history-detail");
  const neg = await SB.api(`/api/negotiations/${id}`);
  detail.innerHTML = `
    <header class="chat-panel__header">
      <div>
        <h2 class="chat-panel__title">${SB.escapeHtml(neg.scenario_title)}</h2>
        <p class="chat-panel__subtitle">
          ${neg.mode === "ai" ? "С нейросетью" : "С человеком"}
          · сложность: ${neg.difficulty}
          · ${statusLabels[neg.status] || neg.status}
        </p>
      </div>
      <span class="chat-panel__status">
        Оценка: <strong>${neg.score != null ? neg.score : "—"}</strong>
      </span>
    </header>
    <div class="chat-messages history-messages">
      ${neg.messages
        .map((m) => {
          const cls =
            m.sender_type === "ai"
              ? "chat-msg chat-msg--bot"
              : m.sender_type === "system"
                ? "chat-msg chat-msg--system"
                : m.is_mine
                  ? "chat-msg chat-msg--user"
                  : "chat-msg chat-msg--bot";
          return `<div class="${cls}">${SB.escapeHtml(m.content)}
            <span class="chat-msg__meta">${SB.formatTime(m.created_at)}</span></div>`;
        })
        .join("")}
    </div>
  `;
}

loadHistory().catch((err) => {
  console.error(err);
  if (err.status === 401) SB.logout();
});
