// ── Hamburger menu ──────────────────────────
const toggle = document.getElementById('navToggle');
const nav    = document.getElementById('mainNav');
if (toggle && nav) {
  toggle.addEventListener('click', () => nav.classList.toggle('open'));
}

// ── Hero Slider ──────────────────────────────
(function () {
  const slides = document.querySelectorAll('.slide');
  if (!slides.length) return;

  const dots   = document.querySelectorAll('.slider-dot');
  let current  = 0;
  let timer;

  function showSlide(n) {
    slides.forEach(s => s.classList.remove('active'));
    dots.forEach(d => d.classList.remove('active'));
    current = (n + slides.length) % slides.length;
    slides[current].classList.add('active');
    if (dots[current]) dots[current].classList.add('active');
  }

  function startTimer() {
    clearInterval(timer);
    timer = setInterval(() => showSlide(current + 1), 5000);
  }

  showSlide(0);
  startTimer();

  const prev = document.querySelector('.slide-prev');
  const next = document.querySelector('.slide-next');
  if (prev) prev.addEventListener('click', () => { showSlide(current - 1); startTimer(); });
  if (next) next.addEventListener('click', () => { showSlide(current + 1); startTimer(); });

  dots.forEach(dot => {
    dot.addEventListener('click', () => {
      showSlide(parseInt(dot.dataset.index));
      startTimer();
    });
  });
})();

// ── Lightbox (zoom de imágenes de artículo) ──
(function () {
  const images = document.querySelectorAll('.article-figure img');
  if (!images.length) return;

  const overlay = document.createElement('div');
  overlay.className = 'lightbox-overlay';
  overlay.innerHTML = '<button class="lightbox-close" aria-label="Cerrar">&times;</button><img src="" alt="" />';
  document.body.appendChild(overlay);

  const overlayImg = overlay.querySelector('img');
  const closeBtn   = overlay.querySelector('.lightbox-close');

  function openLightbox(img) {
    overlayImg.src = img.src;
    overlayImg.alt = img.alt;
    overlay.classList.add('open');
    document.body.style.overflow = 'hidden';
  }

  function closeLightbox() {
    overlay.classList.remove('open');
    document.body.style.overflow = '';
  }

  images.forEach(img => img.addEventListener('click', () => openLightbox(img)));
  overlay.addEventListener('click', closeLightbox);
  closeBtn.addEventListener('click', closeLightbox);
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeLightbox();
  });
})();
