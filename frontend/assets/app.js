/* DocMind — shared client: auth, API, app shell, toast, modal, safe Markdown, icons.
   Loaded by every page as a classic script; exposes a single global: DocMind. */
(function () {
  'use strict';

  const API_BASE = `${window.location.origin}/api/v1`;
  const ACCESS_TOKEN_KEY = 'docmind_access_token';
  const REFRESH_TOKEN_KEY = 'docmind_refresh_token';
  const THEME_KEY = 'docmind_theme';

  // ─── Icons (Lucide-style, inline SVG — no CDN) ────────────────────────────
  const ICON_PATHS = {
    mark: '<rect x="3" y="3" width="8" height="8"/><rect x="13" y="13" width="8" height="8"/><path d="M13 3h8v8"/><path d="M3 13v8h8"/>',
    chat: '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
    file: '<path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><line x1="16" x2="8" y1="13" y2="13"/><line x1="16" x2="8" y1="17" y2="17"/><line x1="10" x2="8" y1="9" y2="9"/>',
    settings: '<line x1="21" x2="14" y1="4" y2="4"/><line x1="10" x2="3" y1="4" y2="4"/><line x1="21" x2="12" y1="12" y2="12"/><line x1="8" x2="3" y1="12" y2="12"/><line x1="21" x2="16" y1="20" y2="20"/><line x1="12" x2="3" y1="20" y2="20"/><line x1="14" x2="14" y1="2" y2="6"/><line x1="8" x2="8" y1="10" y2="14"/><line x1="16" x2="16" y1="18" y2="22"/>',
    plus: '<path d="M5 12h14"/><path d="M12 5v14"/>',
    send: '<path d="m5 12 7-7 7 7"/><path d="M12 19V5"/>',
    copy: '<rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>',
    check: '<path d="M20 6 9 17l-5-5"/>',
    chevron: '<path d="m6 9 6 6 6-6"/>',
    menu: '<line x1="4" x2="20" y1="12" y2="12"/><line x1="4" x2="20" y1="6" y2="6"/><line x1="4" x2="20" y1="18" y2="18"/>',
    x: '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
    logout: '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" x2="9" y1="12" y2="12"/>',
    sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/>',
    moon: '<path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/>',
    upload: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" x2="12" y1="3" y2="15"/>',
    trash: '<path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>',
    pencil: '<path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/>',
    retry: '<path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/>',
    alert: '<circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="8" y2="12"/><line x1="12" x2="12.01" y1="16" y2="16"/>',
    search: '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
    layers: '<path d="m12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83Z"/><path d="m22 17.65-9.17 4.16a2 2 0 0 1-1.66 0L2 17.65"/><path d="m22 12.65-9.17 4.16a2 2 0 0 1-1.66 0L2 12.65"/>',
  };

  function icon(name, extraClass) {
    return `<svg class="icon${extraClass ? ' ' + extraClass : ''}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">${ICON_PATHS[name] || ''}</svg>`;
  }

  // ─── Helpers ──────────────────────────────────────────────────────────────
  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function el(tag, props = {}, ...children) {
    const node = document.createElement(tag);
    for (const [k, v] of Object.entries(props)) {
      if (v === undefined || v === null || v === false) continue;
      if (k === 'class') node.className = v;
      else if (k === 'html') node.innerHTML = v;
      else if (k === 'text') node.textContent = v;
      else if (k.startsWith('on')) node.addEventListener(k.slice(2), v);
      else node.setAttribute(k, v === true ? '' : v);
    }
    node.append(...children.flat().filter((c) => c !== null && c !== undefined && c !== false));
    return node;
  }

  /** Extract a readable message from a FastAPI error body (string detail or 422 array). */
  function errorText(data, fallback) {
    if (data && typeof data.detail === 'string') return data.detail;
    if (data && Array.isArray(data.detail) && data.detail[0]?.msg) return data.detail[0].msg;
    return fallback;
  }

  // ─── Safe Markdown subset ─────────────────────────────────────────────────
  // Escapes everything first, then adds a fixed set of tags — model/document text can never inject HTML.
  // opts.msgId + opts.sourceCount turn [n] markers into chips that point at source cards
  // `${msgId}-src-${n}`; with sourceCount 0 (sources hidden) the markers are dropped.
  function formatInline(escaped, opts = {}) {
    const { msgId, sourceCount = 0, cite = false } = opts;
    let s = escaped.replace(/`([^`]+)`/g, '<code>$1</code>').replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    if (cite) {
      s = s.replace(/(\s?)\[(\d{1,2})\]/g, (m, space, n) => {
        const idx = Number(n);
        if (!sourceCount) return '';
        return idx >= 1 && idx <= sourceCount
          ? `${space}<button type="button" class="cite" data-target="${msgId}-src-${idx}" aria-label="Show source ${idx}">${idx}</button>`
          : m;
      });
    }
    return s;
  }
  const renderInline = (raw, opts) => formatInline(escapeHtml(String(raw ?? '')), opts);

  function renderMarkdown(src, opts = {}) {
    const lines = escapeHtml(String(src).replace(/\r\n/g, '\n')).split('\n');
    const inline = (s) => formatInline(s, opts);
    const out = [];
    let para = [];
    let list = null; // { tag, items }
    let code = null; // string[]

    const flushPara = () => {
      if (para.length) out.push(`<p>${inline(para.join('<br>'))}</p>`);
      para = [];
    };
    const flushList = () => {
      if (list) out.push(`<${list.tag}>${list.items.map((i) => `<li>${inline(i)}</li>`).join('')}</${list.tag}>`);
      list = null;
    };

    for (const line of lines) {
      if (line.trim().startsWith('```')) {
        if (code) { out.push(`<pre><code>${code.join('\n')}</code></pre>`); code = null; }
        else { flushPara(); flushList(); code = []; }
        continue;
      }
      if (code) { code.push(line); continue; }

      const ul = line.match(/^\s*[-*•]\s+(.*)$/);
      const ol = line.match(/^\s*\d+[.)]\s+(.*)$/);
      const h = line.match(/^#{1,6}\s+(.*)$/);

      if (ul || ol) {
        flushPara();
        const tag = ul ? 'ul' : 'ol';
        if (!list || list.tag !== tag) { flushList(); list = { tag, items: [] }; }
        list.items.push((ul || ol)[1]);
      } else if (h) {
        flushPara(); flushList();
        out.push(`<h4>${inline(h[1])}</h4>`);
      } else if (!line.trim()) {
        flushPara(); flushList();
      } else {
        flushList();
        para.push(line);
      }
    }
    if (code) out.push(`<pre><code>${code.join('\n')}</code></pre>`);
    flushPara(); flushList();
    return out.join('');
  }

  // ─── Auth ─────────────────────────────────────────────────────────────────
  const getAccessToken = () => localStorage.getItem(ACCESS_TOKEN_KEY);
  const getRefreshToken = () => localStorage.getItem(REFRESH_TOKEN_KEY);
  function setTokens(access, refresh) {
    localStorage.setItem(ACCESS_TOKEN_KEY, access);
    localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
  }
  function clearTokens() {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  }
  function redirectToLogin() { window.location.href = 'login.html'; }
  function authHeaders(extra = {}) {
    const token = getAccessToken();
    return token ? { ...extra, Authorization: `Bearer ${token}` } : extra;
  }

  async function tryRefreshToken() {
    const refreshToken = getRefreshToken();
    if (!refreshToken) return false;
    try {
      const res = await fetch(`${API_BASE}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
      if (!res.ok) return false;
      const data = await res.json();
      setTokens(data.access_token, data.refresh_token);
      return true;
    } catch {
      return false;
    }
  }

  /** fetch() with the bearer token, one transparent refresh on 401, then redirect to login. */
  async function apiFetch(url, options = {}) {
    let res = await fetch(url, { ...options, headers: authHeaders(options.headers) });
    if (res.status === 401) {
      if (!(await tryRefreshToken())) {
        clearTokens();
        redirectToLogin();
        throw new Error('Session expired. Please sign in again.');
      }
      res = await fetch(url, { ...options, headers: authHeaders(options.headers) });
    }
    return res;
  }

  const api = (path, options) => apiFetch(`${API_BASE}${path}`, options);
  const json = (method, body) => ({ method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });

  async function checkHealth() {
    try {
      const res = await fetch(`${window.location.origin}/health`, { signal: AbortSignal.timeout(4000) });
      return res.ok;
    } catch {
      return false;
    }
  }

  // ─── Toast ────────────────────────────────────────────────────────────────
  function toast(message, type = 'success') {
    let box = document.querySelector('.toasts');
    if (!box) {
      box = el('div', { class: 'toasts', role: 'status', 'aria-live': 'polite' });
      document.body.appendChild(box);
    }
    const t = el('div', { class: `toast ${type}` }, el('span', { html: icon(type === 'error' ? 'alert' : 'check') }), el('span', { text: message }));
    box.appendChild(t);
    setTimeout(() => t.remove(), type === 'error' ? 6000 : 4000);
  }

  // ─── Confirm dialog ───────────────────────────────────────────────────────
  function confirmDialog({ title, message, confirmLabel = 'Confirm', danger = false }) {
    return new Promise((resolve) => {
      const dlg = el('dialog', { class: 'modal', 'aria-labelledby': 'dlgTitle' },
        el('h2', { id: 'dlgTitle', text: title }),
        el('p', { text: message }),
        el('div', { class: 'modal-actions' },
          el('button', { class: 'btn btn-secondary', type: 'button', 'data-act': 'cancel', text: 'Cancel' }),
          el('button', { class: `btn ${danger ? 'btn-danger-solid' : 'btn-primary'}`, type: 'button', 'data-act': 'ok', text: confirmLabel }),
        ),
      );
      let result = false;
      dlg.addEventListener('click', (e) => {
        const act = e.target.closest('[data-act]')?.dataset.act;
        if (act === 'ok') { result = true; dlg.close(); }
        else if (act === 'cancel') dlg.close();
        else if (e.target === dlg) dlg.close();
      });
      dlg.addEventListener('close', () => { dlg.remove(); resolve(result); });
      document.body.appendChild(dlg);
      dlg.showModal();
      dlg.querySelector('[data-act="cancel"]').focus();
    });
  }

  // ─── Theme ────────────────────────────────────────────────────────────────
  const isDark = () => document.documentElement.dataset.theme === 'dark';
  function setTheme(dark) {
    document.documentElement.dataset.theme = dark ? 'dark' : 'light';
    try { localStorage.setItem(THEME_KEY, dark ? 'dark' : 'light'); } catch {}
  }

  // ─── Popover helper (click-outside + Esc) ─────────────────────────────────
  function bindPopover(trigger, panel) {
    const close = () => { panel.hidden = true; trigger.setAttribute('aria-expanded', 'false'); };
    const open = () => { panel.hidden = false; trigger.setAttribute('aria-expanded', 'true'); };
    trigger.setAttribute('aria-haspopup', 'true');
    trigger.setAttribute('aria-expanded', 'false');
    trigger.addEventListener('click', () => (panel.hidden ? open() : close()));
    document.addEventListener('click', (e) => {
      if (!panel.hidden && !panel.contains(e.target) && !trigger.contains(e.target)) close();
    });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && !panel.hidden) { close(); trigger.focus(); }
    });
    return { open, close };
  }

  // ─── App shell ────────────────────────────────────────────────────────────
  const NAV = [
    { id: 'chat', href: 'index.html', label: 'Chat', icon: 'chat' },
    { id: 'documents', href: 'documents.html', label: 'Documents', icon: 'file', admin: true },
    { id: 'settings', href: 'admin.html', label: 'Settings', icon: 'settings', admin: true },
  ];

  /**
   * Build the sidebar + top bar. Returns { main, topbarSlot, setStatus }.
   * opts: { active: 'chat'|'documents'|'settings', title: string, user: {email, role} }
   */
  function mountShell({ active, title, user }) {
    const isAdmin = user.role === 'admin';
    document.title = `${title} — DocMind`;

    const navItems = NAV.filter((n) => !n.admin || isAdmin).map((n) =>
      el('a', { class: 'nav-item', href: n.href, 'aria-current': n.id === active ? 'page' : null, html: `${icon(n.icon)}<span>${n.label}</span>` }),
    );

    const newChat = active === 'chat'
      ? el('button', { class: 'btn btn-primary btn-block', type: 'button', id: 'newChatBtn', html: `${icon('plus')}<span>New chat</span>`, onclick: () => document.dispatchEvent(new CustomEvent('docmind:newchat')) })
      : el('a', { class: 'btn btn-primary btn-block', href: 'index.html', html: `${icon('plus')}<span>New chat</span>` });

    // Account menu
    const accountBtn = el('button', { class: 'account-btn', type: 'button', id: 'accountBtn' },
      el('span', { class: 'avatar', text: (user.email || '?').slice(0, 2), 'aria-hidden': 'true' }),
      el('span', { class: 'account-meta' },
        el('div', { class: 'account-email', text: user.email, title: user.email }),
        el('div', { class: 'account-role', text: user.role }),
      ),
      el('span', { html: icon('chevron') }),
    );
    const themeItem = el('button', { class: 'menu-item', type: 'button' });
    const syncThemeItem = () => { themeItem.innerHTML = `${icon(isDark() ? 'sun' : 'moon')}<span>${isDark() ? 'Light theme' : 'Dark theme'}</span>`; };
    syncThemeItem();
    themeItem.addEventListener('click', () => { setTheme(!isDark()); syncThemeItem(); });
    const logoutItem = el('button', { class: 'menu-item', type: 'button', html: `${icon('logout')}<span>Sign out</span>`, onclick: () => { clearTokens(); redirectToLogin(); } });
    const accountMenu = el('div', { class: 'popover', hidden: true, role: 'menu' }, themeItem, logoutItem);
    const account = el('div', { class: 'account' }, accountMenu, accountBtn);
    bindPopover(accountBtn, accountMenu);

    const sidebar = el('aside', { class: 'sidebar', id: 'sidebar', 'aria-label': 'Primary' },
      el('a', { class: 'brand', href: 'index.html', html: `${icon('mark')}<span>DocMind</span>` }),
      newChat,
      el('nav', { class: 'nav', 'aria-label': 'Main' }, ...navItems),
      el('div', { class: 'sidebar-spacer' }),
      account,
    );

    const scrim = el('div', { class: 'scrim', hidden: true });
    const menuBtn = el('button', { class: 'icon-btn menu-btn', type: 'button', 'aria-label': 'Open navigation', 'aria-controls': 'sidebar', 'aria-expanded': 'false', html: icon('menu') });

    const statusDot = el('span', { class: 'status-dot' });
    const statusText = el('span', { class: 'status-text', text: 'Connecting…' });
    const status = el('span', { class: 'status', role: 'status' }, statusDot, statusText);
    const topbarSlot = el('div', { class: 'topbar-slot' }, el('span', { class: 'topbar-title', text: title }));
    const topbar = el('header', { class: 'topbar' }, menuBtn, topbarSlot, status);
    const main = el('main', { id: 'main' });
    const banner = el('div', { class: 'banner', role: 'alert', hidden: true, html: `${icon('alert')}<span>Can’t reach the server. Check your connection, then retry.</span>` });
    const mainCol = el('div', { class: 'main-col' }, topbar, banner, main);

    // Drawer behaviour (< 768px)
    const setDrawer = (open) => {
      sidebar.classList.toggle('open', open);
      scrim.hidden = !open;
      menuBtn.setAttribute('aria-expanded', String(open));
      if (open) sidebar.querySelector('a, button')?.focus(); else if (document.activeElement && sidebar.contains(document.activeElement)) menuBtn.focus();
    };
    menuBtn.addEventListener('click', () => setDrawer(!sidebar.classList.contains('open')));
    scrim.addEventListener('click', () => setDrawer(false));
    document.addEventListener('keydown', (e) => {
      if (!sidebar.classList.contains('open')) return;
      if (e.key === 'Escape') { setDrawer(false); return; }
      if (e.key === 'Tab') { // focus trap
        const f = [...sidebar.querySelectorAll('a[href], button:not([disabled])')].filter((n) => n.offsetParent !== null);
        if (!f.length) return;
        const first = f[0], last = f[f.length - 1];
        if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
        else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
      }
    });
    window.matchMedia('(min-width: 768px)').addEventListener('change', (m) => { if (m.matches) setDrawer(false); });

    document.body.replaceChildren(el('div', { class: 'shell' }, sidebar, mainCol), scrim);

    return {
      main,
      topbarSlot,
      setStatus(online) {
        status.classList.toggle('offline', !online);
        statusText.textContent = online ? 'Online' : 'Offline';
        banner.hidden = online;
      },
    };
  }

  /** Show a full-page message (used when boot fails, e.g. server unreachable). */
  function renderFatal(message, onRetry) {
    document.body.replaceChildren(
      el('div', { class: 'auth' },
        el('div', { class: 'card auth-card' },
          el('div', { class: 'brand', html: `${icon('mark')}<span>DocMind</span>` }),
          el('div', { class: 'alert', role: 'alert', html: `${icon('alert')}<span>${escapeHtml(message)}</span>` }),
          onRetry ? el('button', { class: 'btn btn-primary btn-block', type: 'button', text: 'Retry', onclick: onRetry }) : null,
        ),
      ),
    );
  }

  /**
   * Ensure there is a signed-in user. Redirects to login when there is no/invalid session.
   * Returns the /auth/me payload, or null if the page is being redirected / showing an error.
   */
  async function requireUser() {
    if (!getAccessToken()) { redirectToLogin(); return null; }
    let res;
    try {
      res = await api('/auth/me');
    } catch (err) {
      if (err instanceof TypeError) { renderFatal('Can’t reach the server.', () => window.location.reload()); }
      return null;
    }
    if (res.status === 401 || res.status === 403) { clearTokens(); redirectToLogin(); return null; }
    if (!res.ok) { renderFatal('The server had a problem. Please try again.', () => window.location.reload()); return null; }
    return res.json();
  }

  window.DocMind = {
    API_BASE, api, apiFetch, json, errorText, escapeHtml, renderMarkdown, renderInline, icon, el,
    getAccessToken, setTokens, clearTokens, redirectToLogin,
    checkHealth, toast, confirmDialog, bindPopover, mountShell, requireUser, renderFatal, setTheme, isDark,
  };
})();
