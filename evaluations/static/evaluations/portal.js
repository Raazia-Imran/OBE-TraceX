'use strict';
const menu = document.querySelector('.menu-button');
menu?.addEventListener('click', () => {
  const expanded = menu.getAttribute('aria-expanded') === 'true';
  menu.setAttribute('aria-expanded', String(!expanded));
  document.querySelector('.sidebar').classList.toggle('open', !expanded);
});
for (const form of document.querySelectorAll('form[data-confirm]')) {
  form.addEventListener('submit', event => {
    if (!window.confirm(form.dataset.confirm)) event.preventDefault();
  });
}
const splash = document.querySelector('.splash');
try {
  if (splash && !sessionStorage.getItem('obe-welcome') && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
    splash.classList.add('show');
    setTimeout(() => splash.classList.remove('show'), 650);
    sessionStorage.setItem('obe-welcome', '1');
  }
} catch (_) { /* Optional welcome animation is skipped if browser storage is unavailable. */ }
