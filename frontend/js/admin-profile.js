if (!SB.requireAuth({ adminOnly: true })) {
  /* redirect */
}

document.getElementById("logout-btn")?.addEventListener("click", () => SB.logout());
document.getElementById("nav-toggle")?.addEventListener("click", () => {
  document.getElementById("nav-links")?.classList.toggle("is-open");
});

async function load() {
  const data = await SB.api("/api/profile/me");
  document.getElementById("profile-status").textContent = data.status;
  await SB.typeText(document.getElementById("profile-name"), data.full_name, { speed: 22 });
  await SB.typeText(document.getElementById("profile-username"), data.username, { speed: 18 });
  await SB.typeText(document.getElementById("profile-email"), data.email, { speed: 12 });
  SB.animateNumber(document.getElementById("profile-age"), data.age, { duration: 900 });

  const form = document.getElementById("profile-edit");
  form.full_name.value = data.full_name;
  form.username.value = data.username;
  form.email.value = data.email;
  form.age.value = data.age;
}

document.getElementById("edit-toggle").onclick = () => {
  const form = document.getElementById("profile-edit");
  const view = document.getElementById("profile-view");
  form.hidden = !form.hidden;
  view.hidden = !form.hidden;
};

document.getElementById("edit-cancel").onclick = () => {
  document.getElementById("profile-edit").hidden = true;
  document.getElementById("profile-view").hidden = false;
};

document.getElementById("profile-edit").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.target;
  const error = document.getElementById("profile-error");
  error.hidden = true;
  const body = {
    full_name: form.full_name.value.trim(),
    username: form.username.value.trim(),
    email: form.email.value.trim(),
    age: Number(form.age.value),
  };
  if (form.password.value) body.password = form.password.value;
  try {
    await SB.api("/api/profile/me", { method: "PATCH", body: JSON.stringify(body) });
    form.hidden = true;
    document.getElementById("profile-view").hidden = false;
    await load();
  } catch (err) {
    error.hidden = false;
    error.textContent = err.message;
  }
});

load().catch((err) => {
  if (err.status === 401 || err.status === 403) SB.logout();
});
