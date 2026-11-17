// Runs synchronously in <head> so the theme is applied before first paint (no flash).
// Light is the default and the OS/browser colour-scheme is deliberately NOT followed:
// dark mode is opt-in via "Dark theme" in the account menu, and that choice is remembered.
(function () {
  var saved = null;
  try { saved = localStorage.getItem('docmind_theme'); } catch (e) {}
  document.documentElement.dataset.theme = saved === 'dark' ? 'dark' : 'light';
})();
