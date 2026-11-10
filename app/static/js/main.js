/* =========================================================
   CHERE — main.js
   Dark/Light mode, compteurs animés, navbar scroll, carte Leaflet
   ========================================================= */

document.addEventListener("DOMContentLoaded", () => {
  initThemeToggle();
  initNavbarScroll();
  initMobileMenu();
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

  const themeToggleMobile = document.getElementById("theme-toggle-mobile");
  if (themeToggleMobile) {
    themeToggleMobile.addEventListener("click", () => {
      const current = root.getAttribute("data-theme");
      const next = current === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      localStorage.setItem("chere-theme", next);
      updateToggleIcon(next);
    });
  }
}

function updateToggleIcon(theme) {
  const iconDesktop = document.querySelector("#theme-toggle i");
  const iconMobile = document.querySelector("#theme-toggle-mobile i");
  const cls = theme === "dark" ? "bi bi-sun-fill" : "bi bi-moon-stars-fill";
  if (iconDesktop) iconDesktop.className = cls;
  if (iconMobile) iconMobile.className = cls;
}

/* ---------- Navbar au scroll ---------- */
function initNavbarScroll() {
  const nav = document.querySelector(".navbar-modern");
  if (!nav) return;
  window.addEventListener("scroll", () => {
    nav.classList.toggle("shadow-chere", window.scrollY > 20);
  });
}

/* ---------- Menu mobile hamburger ---------- */
function initMobileMenu() {
  const toggleBtn = document.getElementById("navMobileToggle");
  const closeBtn = document.getElementById("navMobileClose");
  const overlay = document.getElementById("navMobileOverlay");
  const mobileLinks = document.querySelectorAll(".nav-mobile-link");
  const html = document.documentElement;

  if (!toggleBtn || !closeBtn || !overlay) return;

  const openMenu = () => {
    overlay.classList.add("open");
    toggleBtn.setAttribute("aria-expanded", "true");
    html.style.overflow = "hidden";
  };

  const closeMenu = () => {
    overlay.classList.remove("open");
    toggleBtn.setAttribute("aria-expanded", "false");
    html.style.overflow = "";
  };

  toggleBtn.addEventListener("click", openMenu);
  closeBtn.addEventListener("click", closeMenu);

  // Fermer en cliquant sur un lien
  mobileLinks.forEach((link) => {
    link.addEventListener("click", closeMenu);
  });

  // Fermer en cliquant sur le fond (overlay)
  overlay.addEventListener("click", (e) => {
    if (e.target === overlay) closeMenu();
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
