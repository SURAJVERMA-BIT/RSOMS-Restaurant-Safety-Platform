/* ═══════════════════════════════════════════════
   RSOMS — Main Frontend JavaScript
   ═══════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', function () {

  // ── Auto-dismiss flash alerts after 5s ──
  setTimeout(function () {
    document.querySelectorAll('.alert.alert-dismissible').forEach(function (alert) {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) bsAlert.close();
    });
  }, 5000);

  // ── Fade-in animation on scroll ──
  const fadeEls = document.querySelectorAll('.fade-in');
  if (fadeEls.length > 0) {
    const observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1 });
    fadeEls.forEach(function (el) { observer.observe(el); });
  }

  // ── Animate stat card numbers on load ──
  document.querySelectorAll('.stat-value').forEach(function (el) {
    const target = parseFloat(el.textContent);
    if (isNaN(target)) return;
    let current = 0;
    const step = target / 40;
    const timer = setInterval(function () {
      current = Math.min(current + step, target);
      el.textContent = Number.isInteger(target) ? Math.floor(current) : current.toFixed(1);
      if (current >= target) clearInterval(timer);
    }, 30);
  });

  // ── Score bar animate on load ──
  document.querySelectorAll('.score-bar-fill').forEach(function (bar) {
    const w = bar.style.width;
    bar.style.width = '0%';
    setTimeout(function () { bar.style.width = w; }, 300);
  });

  // ── Toggle availability form — prevent full reload ──
  document.querySelectorAll('.toggle-form').forEach(function (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      const btn = form.querySelector('button[type="submit"]');
      const origText = btn.textContent;
      btn.disabled = true;
      btn.textContent = '...';

      fetch(form.action, {
        method: 'POST',
        body: new FormData(form)
      })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (data.status === 'ok') {
            btn.style.background = data.available ? '#d5f5e3' : '#fdedec';
            btn.style.color = data.available ? '#1e8449' : '#922b21';
            btn.textContent = data.available ? '✓ Available' : '✗ Unavailable';
          }
          btn.disabled = false;
        })
        .catch(function () {
          btn.disabled = false;
          btn.textContent = origText;
        });
    });
  });

  // ── Tooltip init ──
  const tooltipTriggers = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  tooltipTriggers.forEach(function (el) {
    new bootstrap.Tooltip(el);
  });

  // ── Checklist: mark row visual on checkbox click ──
  document.querySelectorAll('.checklist-item input[type="checkbox"]').forEach(function (cb) {
    cb.addEventListener('change', function () {
      const row = cb.closest('.checklist-item');
      if (row) row.classList.toggle('checked', cb.checked);
    });
  });

  // ── KDS countdown display ──
  const kdsCountdown = document.querySelector('[data-kds-refresh]');
  if (kdsCountdown) {
    let remaining = parseInt(kdsCountdown.dataset.kdsRefresh || 30);
    setInterval(function () {
      remaining--;
      if (remaining <= 0) {
        remaining = 30;
      }
      kdsCountdown.textContent = 'Auto-refreshes in ' + remaining + 's';
    }, 1000);
  }

  // ── Score bar progress animation for analytics ──
  document.querySelectorAll('[data-progress]').forEach(function (el) {
    const pct = parseFloat(el.dataset.progress);
    if (!isNaN(pct)) {
      setTimeout(function () { el.style.width = pct + '%'; }, 400);
    }
  });

  // ── Confirm dangerous actions ──
  document.querySelectorAll('[data-confirm]').forEach(function (el) {
    el.addEventListener('click', function (e) {
      if (!confirm(el.dataset.confirm)) e.preventDefault();
    });
  });

  // ── Password show/hide toggle (CSP-safe, data-attribute based) ──
  document.querySelectorAll('[data-toggle-pass]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      const input = document.getElementById(btn.getAttribute('data-toggle-pass'));
      if (!input) return;
      const icon = btn.querySelector('i');
      const reveal = input.type === 'password';
      input.type = reveal ? 'text' : 'password';
      if (icon) icon.className = reveal ? 'fa-regular fa-eye-slash' : 'fa-regular fa-eye';
    });
  });

});

// ── Global helper: format currency ──
function formatINR(amount) {
  return '₹' + parseFloat(amount).toLocaleString('en-IN', { minimumFractionDigits: 2 });
}
