if (SB.isAuthed()) {
  location.replace(SB.role === "admin" ? "/admin.html" : "/index.html");
}

document.getElementById("login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.target;
  const error = document.getElementById("login-error");
  error.hidden = true;
  try {
    const data = await SB.api("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({
        login: form.login.value.trim(),
        password: form.password.value,
      }),
    });
    SB.setSession(data.access_token, data.role);
    location.replace(data.role === "admin" ? "/admin.html" : "/index.html");
  } catch (err) {
    error.hidden = false;
    error.textContent = err.message;
  }
});
