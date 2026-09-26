/**
 * Ранний редирект до отрисовки страницы (localStorage).
 * Подключать в <head> защищённых страниц.
 *
 * data-sb-gate:
 *   user  — только обычный пользователь (index/profile/history)
 *   admin — только админ
 *   any   — любой авторизованный
 */
(function () {
  var html = document.documentElement;
  html.classList.add("sb-gate");

  var script = document.currentScript;
  var gate = (script && script.getAttribute("data-sb-gate")) || "user";
  var token = localStorage.getItem("sb_token");
  var role = localStorage.getItem("sb_role");

  if (!token) {
    location.replace("/auth.html");
    return;
  }

  if (gate === "user" && role === "admin") {
    location.replace("/admin.html");
    return;
  }

  if (gate === "admin" && role !== "admin") {
    location.replace("/index.html");
    return;
  }

  html.classList.add("sb-authed");
})();
