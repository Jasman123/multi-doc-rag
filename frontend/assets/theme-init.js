// Runs synchronously in <head> so the theme is applied before first paint (no flash).
(function () {
  var saved = null;
  try { saved = localStorage.getItem('docmind_theme'); } catch (e) {}
  var dark = saved ? saved === 'dark' : window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  document.documentElement.dataset.theme = dark ? 'dark' : 'light';
})();
