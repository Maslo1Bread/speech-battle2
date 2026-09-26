if (!SB.requireAuth({ userOnly: true })) {
  /* redirect */
}

document.getElementById("logout-btn")?.addEventListener("click", () => SB.logout());
document.getElementById("nav-toggle")?.addEventListener("click", () => {
  document.getElementById("nav-links")?.classList.toggle("is-open");
});

let profileData = null;

async function loadProfile() {
  profileData = await SB.api("/api/profile/me");
  await renderProfile(profileData);
}

async function renderProfile(data) {
  document.getElementById("profile-status").textContent =
    data.status === "active" ? "активен" : data.status;

  await SB.typeText(document.getElementById("profile-name"), data.full_name, { speed: 22 });
  await SB.typeText(document.getElementById("profile-username"), data.username, { speed: 18 });
  await SB.typeText(document.getElementById("profile-email"), data.email, { speed: 12 });
  SB.animateNumber(document.getElementById("profile-age"), data.age, { duration: 900 });
  SB.animateNumber(document.getElementById("score-value"), Math.round(data.overall_score || 0), {
    duration: 1400,
  });
  drawWeekChart(data.week_scores || []);

  const form = document.getElementById("profile-edit");
  form.full_name.value = data.full_name;
  form.username.value = data.username;
  form.email.value = data.email;
  form.age.value = data.age;
  form.password.value = "";
}

function drawWeekChart(points) {
  const canvas = document.getElementById("week-chart");
  const empty = document.getElementById("chart-empty");
  const ctx = canvas.getContext("2d");
  const dpr = window.devicePixelRatio || 1;
  const width = canvas.clientWidth || 640;
  const height = 240;
  canvas.width = width * dpr;
  canvas.height = height * dpr;
  ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, width, height);

  if (!points.length) {
    empty.hidden = false;
    return;
  }
  empty.hidden = true;

  const pad = 28;
  const values = points.map((p) => p.score);
  const maxY = Math.max(100, ...values);
  const stepX = values.length === 1 ? 0 : (width - pad * 2) / (values.length - 1);

  // animate line draw
  const coords = values.map((v, i) => ({
    x: pad + i * stepX,
    y: height - pad - (v / maxY) * (height - pad * 2),
  }));

  let progress = 0;
  const animate = () => {
    progress = Math.min(1, progress + 0.03);
    ctx.clearRect(0, 0, width, height);

    ctx.strokeStyle = "rgba(107,79,160,0.2)";
    ctx.lineWidth = 1;
    for (let y = 0; y <= 100; y += 25) {
      const yy = height - pad - (y / maxY) * (height - pad * 2);
      ctx.beginPath();
      ctx.moveTo(pad, yy);
      ctx.lineTo(width - pad, yy);
      ctx.stroke();
    }

    const visible = Math.max(2, Math.floor(coords.length * progress));
    ctx.beginPath();
    ctx.strokeStyle = "#6b4fa0";
    ctx.lineWidth = 3;
    ctx.lineJoin = "round";
    coords.slice(0, visible).forEach((pt, i) => {
      if (i === 0) ctx.moveTo(pt.x, pt.y);
      else ctx.lineTo(pt.x, pt.y);
    });
    ctx.stroke();

    coords.slice(0, visible).forEach((pt) => {
      ctx.beginPath();
      ctx.fillStyle = "#8b6fc0";
      ctx.arc(pt.x, pt.y, 4, 0, Math.PI * 2);
      ctx.fill();
    });

    if (progress < 1) requestAnimationFrame(animate);
  };
  requestAnimationFrame(animate);
}

const editToggle = document.getElementById("edit-toggle");
const editForm = document.getElementById("profile-edit");
const view = document.getElementById("profile-view");

editToggle.addEventListener("click", () => {
  editForm.hidden = !editForm.hidden;
  view.hidden = !editForm.hidden;
});

document.getElementById("edit-cancel").addEventListener("click", () => {
  editForm.hidden = true;
  view.hidden = false;
});

editForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const error = document.getElementById("profile-error");
  error.hidden = true;
  const body = {
    full_name: editForm.full_name.value.trim(),
    username: editForm.username.value.trim(),
    email: editForm.email.value.trim(),
    age: Number(editForm.age.value),
  };
  if (editForm.password.value) body.password = editForm.password.value;
  try {
    profileData = await SB.api("/api/profile/me", {
      method: "PATCH",
      body: JSON.stringify(body),
    });
    editForm.hidden = true;
    view.hidden = false;
    await renderProfile(profileData);
  } catch (err) {
    error.hidden = false;
    error.textContent = err.message;
  }
});

loadProfile().catch((err) => {
  console.error(err);
  if (err.status === 401) SB.logout();
});
