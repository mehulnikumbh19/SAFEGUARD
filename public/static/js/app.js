document.addEventListener("DOMContentLoaded", () => {
  /* ----- Theme toggle (persists in localStorage) ----- */
  const toggle = document.getElementById("theme-toggle");
  if (toggle) {
    toggle.addEventListener("click", () => {
      const current = document.documentElement.getAttribute("data-theme") || "dark";
      const next = current === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", next);
      try { localStorage.setItem("safeguard-theme", next); } catch (e) {}
      window.dispatchEvent(new CustomEvent("safeguard:theme-change", { detail: { theme: next } }));
    });
  }

  /* ----- Mobile sidebar toggle ----- */
  const menuBtn = document.getElementById("menu-btn");
  const sidebar = document.getElementById("sidebar");
  if (menuBtn && sidebar) {
    menuBtn.addEventListener("click", () => sidebar.classList.toggle("open"));
    sidebar.querySelectorAll(".nav-pill").forEach((link) =>
      link.addEventListener("click", () => sidebar.classList.remove("open"))
    );
  }

  /* ----- Table search input (rendered above any .searchable table) ----- */
  document.querySelectorAll(".searchable").forEach((table) => {
    const wrap = document.createElement("div");
    wrap.className = "search-pill";
    wrap.style.marginBottom = "12px";
    wrap.style.maxWidth = "320px";
    wrap.innerHTML = '<i class="bi bi-search"></i>';

    const input = document.createElement("input");
    input.type = "search";
    input.placeholder = "Search this table…";
    wrap.appendChild(input);

    const host = table.closest(".table-wrap") || table;
    host.parentElement.insertBefore(wrap, host);

    input.addEventListener("input", () => {
      const needle = input.value.toLowerCase();
      table.querySelectorAll("tbody tr").forEach((row) => {
        row.style.display = row.textContent.toLowerCase().includes(needle) ? "" : "none";
      });
    });
  });

  /* ----- Confirm dialogs for any form with data-confirm ----- */
  document.querySelectorAll("form[data-confirm]").forEach((form) => {
    form.addEventListener("submit", (event) => {
      if (!window.confirm(form.dataset.confirm)) event.preventDefault();
    });
  });

  /* ----- Auto-submit inline forms when their input changes (debounced) ----- */
  document.querySelectorAll(".inline-form input").forEach((input) => {
    let timer;
    input.addEventListener("input", () => {
      clearTimeout(timer);
      timer = setTimeout(() => input.form.submit(), 700);
    });
  });

  /* ----- Auto-dismiss alerts after 5s ----- */
  document.querySelectorAll(".alert").forEach((alert) => {
    setTimeout(() => alert.classList.add("fade"), 5000);
    setTimeout(() => alert.remove(), 5600);
  });
});
