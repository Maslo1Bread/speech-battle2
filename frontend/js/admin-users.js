if (!SB.requireAuth({ adminOnly: true })) {
  /* redirect */
}

document.getElementById("logout-btn")?.addEventListener("click", () => SB.logout());
document.getElementById("nav-toggle")?.addEventListener("click", () => {
  document.getElementById("nav-links")?.classList.toggle("is-open");
});

let allUsers = [];

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
      const label =
        m.sender_label ||
        (m.sender_type === "ai" ? "Нейросеть" : m.sender_type === "system" ? "Система" : "Участник");
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

async function loadUsers(q = "") {
  const query = q ? `?q=${encodeURIComponent(q)}` : "";
  allUsers = await SB.api(`/api/admin/users${query}`);
  const list = document.getElementById("users-list");
  if (!allUsers.length) {
    list.innerHTML = `<li class="history-empty">Никого не найдено</li>`;
    return;
  }
  list.innerHTML = allUsers
    .map(
      (u) => `
      <li>
        <button type="button" class="history-item" data-id="${u.id}">
          <span class="history-item__title">${SB.escapeHtml(u.full_name)} (@${SB.escapeHtml(u.username)})</span>
          <span class="history-item__meta">${SB.escapeHtml(u.email)} · ${u.role} · ${u.status}${
            u.pii_ok === false ? " · данные повреждены (SECRET_KEY)" : ""
          }</span>
          <span class="history-item__date">Оценка: ${Math.round(u.overall_score || 0)}</span>
        </button>
      </li>`,
    )
    .join("");
}

document.getElementById("users-list").addEventListener("click", async (event) => {
  const btn = event.target.closest(".history-item");
  if (!btn) return;
  await openUser(Number(btn.dataset.id));
});

let searchTimer;
document.getElementById("user-search").addEventListener("input", (event) => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => loadUsers(event.target.value.trim()), 250);
});

document.getElementById("create-user-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.target;
  const error = document.getElementById("create-user-error");
  const ok = document.getElementById("create-user-ok");
  error.hidden = true;
  ok.hidden = true;
  try {
    await SB.api("/api/admin/users", {
      method: "POST",
      body: JSON.stringify({
        full_name: form.full_name.value.trim(),
        username: form.username.value.trim(),
        email: form.email.value.trim(),
        age: Number(form.age.value),
        password: form.password.value,
        is_admin: Boolean(form.is_admin.checked),
      }),
    });
    form.reset();
    ok.hidden = false;
    await loadUsers(document.getElementById("user-search").value.trim());
  } catch (err) {
    error.hidden = false;
    error.textContent = err.message;
  }
});

async function openUser(id) {
  const panel = document.getElementById("users-panel");
  const detail = document.getElementById("user-detail");
  const data = await SB.api(`/api/admin/users/${id}`);
  panel.hidden = true;
  detail.hidden = false;
  detail.innerHTML = `
    <section class="sb-surface profile-hero">
      <button class="sb-btn sb-btn--ghost" type="button" id="back-users">← К списку</button>
      <div class="profile-hero__top" style="margin-top:1rem">
        <div>
          <p class="profile-kicker">Профиль пользователя</p>
          <h1 class="profile-name">${SB.escapeHtml(data.full_name)}</h1>
          <p class="profile-status">Статус: <strong>${SB.escapeHtml(data.status)}</strong> · роль: ${data.role}</p>
          ${
            data.pii_ok === false
              ? `<p class="form-error" style="display:block">PII не расшифровывается (менялся SECRET_KEY). Сохраните новые логин/почту/имя — данные перезапишутся.</p>`
              : ""
          }
        </div>
      </div>
      <form class="auth-form" id="admin-user-form">
        <label class="sb-field"><span>Имя</span><input class="sb-input" name="full_name" value="${SB.escapeHtml(data.full_name)}" required></label>
        <label class="sb-field"><span>Юзернейм</span><input class="sb-input" name="username" value="${SB.escapeHtml(data.username)}" required></label>
        <label class="sb-field"><span>Почта</span><input class="sb-input" type="email" name="email" value="${SB.escapeHtml(data.email === "—" ? "" : data.email)}" required></label>
        <label class="sb-field"><span>Возраст</span><input class="sb-input" type="number" name="age" value="${data.age}" min="14" max="100" required></label>
        <label class="sb-field"><span>Статус</span>
          <select class="sb-input" name="status">
            <option value="active" ${data.status === "active" ? "selected" : ""}>active</option>
            <option value="blocked" ${data.status === "blocked" ? "selected" : ""}>blocked</option>
          </select>
        </label>
        <label class="sb-field"><span>Новый пароль</span><input class="sb-input" type="password" name="password" minlength="6"></label>
        <p class="form-error" id="user-edit-error" hidden></p>
        <button class="sb-btn sb-btn--primary" type="submit">Сохранить</button>
      </form>
      <p class="profile-status">Общая оценка: <strong>${Math.round(data.overall_score || 0)}</strong></p>
    </section>

    <section class="sb-surface history-list-panel" style="margin-top:1rem">
      <header class="scenarios__header">
        <h2 class="scenarios__title">История переговоров</h2>
      </header>
      <ul class="history-list" id="user-neg-list">
        ${(data.negotiations || [])
          .map(
            (n) => `
          <li>
            <button type="button" class="history-item" data-neg="${n.id}">
              <span class="history-item__title">${SB.escapeHtml(n.scenario_title)}</span>
              <span class="history-item__meta">${n.mode} · ${n.difficulty} · ${n.status} ${n.score != null ? `· ${n.score}` : ""}</span>
            </button>
          </li>`,
          )
          .join("") || `<li class="history-empty">Нет переговоров</li>`}
      </ul>
    </section>
    <section class="sb-surface history-detail" id="user-neg-detail" style="margin-top:1rem">
      <div class="chat-empty">Выберите чат</div>
    </section>
  `;

  document.getElementById("back-users").onclick = () => {
    detail.hidden = true;
    panel.hidden = false;
  };

  document.getElementById("admin-user-form").onsubmit = async (event) => {
    event.preventDefault();
    const form = event.target;
    const error = document.getElementById("user-edit-error");
    error.hidden = true;
    const body = {
      full_name: form.full_name.value.trim(),
      username: form.username.value.trim(),
      email: form.email.value.trim(),
      age: Number(form.age.value),
      status: form.status.value,
    };
    if (form.password.value) body.password = form.password.value;
    try {
      await SB.api(`/api/admin/users/${id}`, { method: "PATCH", body: JSON.stringify(body) });
      await openUser(id);
    } catch (err) {
      error.hidden = false;
      error.textContent = err.message;
    }
  };

  document.getElementById("user-neg-list").onclick = async (event) => {
    const btn = event.target.closest("[data-neg]");
    if (!btn) return;
    const negId = Number(btn.dataset.neg);
    const neg = await SB.api(`/api/admin/reviews/${negId}`);
    const participants = neg.participants || [];
    const box = document.getElementById("user-neg-detail");
    box.innerHTML = `
      <header class="chat-panel__header">
        <div>
          <h2 class="chat-panel__title">${SB.escapeHtml(neg.scenario_title)}</h2>
          <p class="chat-panel__subtitle">${neg.mode === "ai" ? `нейросеть · ${neg.difficulty}` : "человек"}</p>
        </div>
      </header>
      <div class="chat-messages history-messages">
        ${renderMessages(neg.messages, neg.participant1_id, neg.participant2_id)}
      </div>
      <form class="score-form" id="user-score-form">
        ${scoreFieldsHtml(participants, neg.score || 70)}
        <button class="sb-btn sb-btn--primary" type="submit">Обновить оценку</button>
        <p class="form-error" id="user-score-error" hidden></p>
        <p class="form-ok" id="user-score-ok" hidden>Оценка обновлена</p>
      </form>
    `;
    document.getElementById("user-score-form").onsubmit = async (ev) => {
      ev.preventDefault();
      const errEl = document.getElementById("user-score-error");
      const okEl = document.getElementById("user-score-ok");
      errEl.hidden = true;
      okEl.hidden = true;
      try {
        await SB.api(`/api/admin/reviews/${negId}/score`, {
          method: "POST",
          body: JSON.stringify(scoresPayloadFromForm(ev.target, participants)),
        });
        okEl.hidden = false;
        await openUser(id);
      } catch (err) {
        errEl.hidden = false;
        errEl.textContent = err.message;
      }
    };
  };
}

loadUsers().catch((err) => {
  const list = document.getElementById("users-list");
  if (list) {
    list.innerHTML = `<li class="history-empty">Ошибка загрузки: ${SB.escapeHtml(err.message || "unknown")}</li>`;
  }
  if (err.status === 401 || err.status === 403) SB.logout();
});
