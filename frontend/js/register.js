if (SB.isAuthed()) {
  location.replace(SB.role === "admin" ? "/admin.html" : "/index.html");
}

document.getElementById("register-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.target;
  const error = document.getElementById("register-error");
  error.hidden = true;
  try {
    const data = await SB.api("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({
        full_name: form.full_name.value.trim(),
        username: form.username.value.trim(),
        email: form.email.value.trim(),
        age: Number(form.age.value),
        password: form.password.value,
      }),
    });
    SB.setSession(data.access_token, data.role);
    location.replace("/index.html");
  } catch (err) {
    error.hidden = false;
    error.textContent = err.message;
  }
});
