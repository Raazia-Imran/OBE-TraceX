'use strict';
(() => {
  document.querySelectorAll('[data-brand-replay]').forEach(button => button.addEventListener('click', () => {
    document.querySelectorAll('.brand-writing .written-brand').forEach(brand => { const copy = brand.cloneNode(true); brand.replaceWith(copy); });
  }));
  const choicePanel = document.querySelector('.privacy-choice');
  const consentKey = 'obe-privacy-choice';
  const rememberKey = 'obe-intro-seen';
  const remember = document.querySelector('[data-story-remember]');
  let preferences = false;
  function storedChoice() {
    try {
      const value = JSON.parse(localStorage.getItem(consentKey));
      if (value && ['essential', 'preferences'].includes(value.mode) && Date.now() - value.at < 180 * 86400000) return value.mode;
    } catch (_) { /* Storage may be disabled. */ }
    return null;
  }
  function applyChoice(mode) {
    preferences = mode === 'preferences';
    if (remember) {
      remember.parentElement.hidden = !preferences;
      try { remember.checked = preferences && localStorage.getItem(rememberKey) === '1'; } catch (_) { remember.checked = false; }
    }
    if (!preferences) { try { localStorage.removeItem(rememberKey); } catch (_) { /* No storage. */ } }
    for (const link of document.querySelectorAll('[data-watch-intro]')) {
      try { link.textContent = preferences && localStorage.getItem(rememberKey) ? 'Replay the 36-second story →' : 'Watch the 36-second story →'; } catch (_) { /* Default text remains. */ }
    }
  }
  const saved = storedChoice();
  applyChoice(saved);
  if (choicePanel) choicePanel.hidden = Boolean(saved);
  document.querySelectorAll('[data-privacy]').forEach(button => button.addEventListener('click', () => {
    const mode = button.dataset.privacy;
    try { localStorage.setItem(consentKey, JSON.stringify({mode, at: Date.now()})); } catch (_) { /* Choice applies for this page. */ }
    applyChoice(mode);
    if (choicePanel) choicePanel.hidden = true;
  }));
  document.querySelectorAll('[data-privacy-open]').forEach(button => button.addEventListener('click', () => {
    if (choicePanel) { choicePanel.hidden = false; choicePanel.querySelector('button')?.focus(); }
  }));
  remember?.addEventListener('change', () => {
    if (preferences) { try { remember.checked ? localStorage.setItem(rememberKey, '1') : localStorage.removeItem(rememberKey); } catch (_) { /* No storage. */ } }
  });
  const loader = document.querySelector('.work-loader');
  document.addEventListener('submit', event => {
    if (event.defaultPrevented || !loader || event.target.method.toLowerCase() !== 'post') return;
    loader.hidden = false;
    event.target.setAttribute('aria-busy', 'true');
  });
  window.addEventListener('pageshow', () => { if (loader) loader.hidden = true; document.querySelectorAll('[aria-busy="true"]').forEach(form => form.removeAttribute('aria-busy')); });

  const player = document.querySelector('.walkthrough');
  if (!player) return;
  player.dataset.ready = 'true';
  const scenes = [...player.querySelectorAll('[data-scene]')];
  const chapters = [...player.querySelectorAll('[data-chapter]')];
  const play = player.querySelector('[data-story-play]');
  const seek = player.querySelector('[data-story-seek]');
  const clock = player.querySelector('[data-story-time]');
  const caption = player.querySelector('[data-story-caption]');
  let time = 0, playing = false, previous = 0, frame = 0, scene = -1;
  function paint() {
    const next = Math.min(5, Math.floor(time / 6));
    if (next !== scene) {
      scene = next;
      player.dataset.scene = String(scene);
      scenes.forEach((item, index) => { item.hidden = index !== scene; });
      chapters.forEach((button, index) => { button.setAttribute('aria-current', index === scene ? 'step' : 'false'); });
      caption.textContent = scenes[scene].querySelector('p').textContent;
    }
    seek.value = String(time);
    clock.textContent = `0:${String(Math.floor(time)).padStart(2, '0')} / 0:36`;
    play.textContent = playing ? 'Pause story' : time >= 36 ? 'Replay story' : time > 0 ? 'Continue story' : 'Play the story';
    play.setAttribute('aria-pressed', String(playing));
    player.classList.toggle('is-playing', playing);
  }
  function tick(now) {
    if (!playing) return;
    time = Math.min(36, time + Math.max(0, now - previous) / 1000);
    previous = now;
    if (time >= 36) playing = false;
    paint();
    if (playing) frame = requestAnimationFrame(tick);
  }
  function pause() { playing = false; cancelAnimationFrame(frame); paint(); }
  function start() { if (time >= 36) time = 0; playing = true; previous = performance.now(); paint(); frame = requestAnimationFrame(tick); }
  play.addEventListener('click', () => playing ? pause() : start());
  player.querySelector('[data-story-replay]').addEventListener('click', () => { pause(); time = 0; start(); });
  seek.addEventListener('input', () => { const selected = Number(seek.value); pause(); time = selected; paint(); });
  chapters.forEach(button => button.addEventListener('click', () => { pause(); time = Number(button.dataset.chapter) * 6; paint(); }));
  document.addEventListener('visibilitychange', () => { if (document.hidden) pause(); });
  window.addEventListener('pagehide', pause);
  paint();
})();
