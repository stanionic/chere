/* =========================================================
   CHERE — main.js
   Dark/Light mode, compteurs animés, navbar scroll, carte Leaflet
   ========================================================= */

document.addEventListener("DOMContentLoaded", () => {
  initThemeToggle();
  initNavbarScroll();
  initCounters();
  initWorldMap();
});

/* ---------- Dark / Light mode ---------- */
function initThemeToggle() {
  const root = document.documentElement;
  const toggleBtn = document.getElementById("theme-toggle");
  const stored = localStorage.getItem("chere-theme");
  const preferred = stored || (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  root.setAttribute("data-theme", preferred);
  updateToggleIcon(preferred);

  if (toggleBtn) {
    toggleBtn.addEventListener("click", () => {
      const current = root.getAttribute("data-theme");
      const next = current === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      localStorage.setItem("chere-theme", next);
      updateToggleIcon(next);
    });
  }
}

function updateToggleIcon(theme) {
  const icon = document.querySelector("#theme-toggle i");
  if (!icon) return;
  icon.className = theme === "dark" ? "bi bi-sun-fill" : "bi bi-moon-stars-fill";
}

/* ---------- Navbar au scroll ---------- */
function initNavbarScroll() {
  const nav = document.querySelector(".navbar-chere");
  if (!nav) return;
  window.addEventListener("scroll", () => {
    nav.classList.toggle("shadow-chere", window.scrollY > 20);
  });
}

/* ---------- Compteurs animés ---------- */
function initCounters() {
  const counters = document.querySelectorAll(".js-counter");
  if (!counters.length) return;

  const animate = (el) => {
    const target = parseInt(el.dataset.target, 10) || 0;
    const duration = 1600;
    const start = performance.now();

    const step = (now) => {
      const progress = Math.min((now - start) / duration, 1);
      const value = Math.floor(progress * target);
      el.textContent = value.toLocaleString("fr-FR");
      if (progress < 1) requestAnimationFrame(step);
      else el.textContent = target.toLocaleString("fr-FR");
    };
    requestAnimationFrame(step);
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        animate(entry.target);
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.4 });

  counters.forEach((c) => observer.observe(c));
}

/* ---------- Carte interactive du monde (Leaflet) ---------- */
function initWorldMap() {
  const mapEl = document.getElementById("world-map");
  if (!mapEl || typeof L === "undefined") return;

  const map = L.map("world-map", {
    worldCopyJump: true,
    zoomControl: true,
    minZoom: 1.5,
  }).setView([15, 10], 2);

  L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", {
    attribution: '&copy; OpenStreetMap &copy; CARTO',
  }).addTo(map);

  fetch("/api/v1/projects/map")
    .then((res) => res.json())
    .then((projects) => {
      projects.forEach((p) => {
        if (!p.lat || !p.lng) return;
        const marker = L.circleMarker([p.lat, p.lng], {
          radius: 8,
          color: "#d4a017",
          fillColor: "#1446a0",
          fillOpacity: 0.85,
          weight: 2,
        }).addTo(map);
        marker.bindPopup(`<strong>${p.title}</strong><br>${p.country || ""}`);
      });
    })
    .catch(() => { /* silencieux : la carte reste affichée sans marqueurs */ });
}
