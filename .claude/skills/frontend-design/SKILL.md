---
name: frontend-design
description: Conventions for designing or changing the plain HTML/JS frontend in frontend/ (chat, login, documents, settings pages) — shared assets, design tokens, app shell, auth/API pattern. Use when adding or restyling any frontend page or component.
---

# Frontend design — DocMind

Framework-free pages in `frontend/` (`index.html` chat, `login.html`, `documents.html`, `admin.html`
= Settings) share one design system in `frontend/assets/`. No build step. FastAPI serves the folder
as static files (`backend/app/main.py`, `StaticFiles(..., html=True)` at `/`), so pages and API share
an origin. The design spec lives in `docs/design/enterprise-chat-redesign/DESIGN.md` (note: `docs/`
is gitignored) — read it before changing the look.

## Files

- `assets/app.css` — tokens (light + dark), base, shell, components. **All styling goes here**; pages have no inline `<style>`.
- `assets/theme-init.js` — loaded synchronously in `<head>` to set `data-theme` before paint (`localStorage` key `docmind_theme`).
- `assets/app.js` — global `DocMind`: `requireUser`, `mountShell`, `api`/`apiFetch` (bearer + one refresh on 401), `toast`, `confirmDialog`, `renderMarkdown` (escape-first safe subset), `icon(name)`, `el(tag, props, ...children)`.
- `assets/fonts/` — self-hosted Inter and JetBrains Mono (OFL licences included). No external font/CDN requests.

## Page skeleton

```html
<head> … <script src="assets/theme-init.js"></script><link rel="stylesheet" href="assets/app.css"> </head>
<body>
<script src="assets/app.js"></script>
<script>
(async () => {
  const user = await DocMind.requireUser();           // redirects to login.html if not signed in
  if (!user) return;
  const shell = DocMind.mountShell({ active: 'chat' | 'documents' | 'settings', title: '…', user });
  // build UI into shell.main (wrap content in <div class="page"> for non-chat pages)
})();
</script>
```

Role gating is UI-only (nav hides admin items; admin pages show an "Administrator access required"
state) — the backend enforces it. Build DOM with `el()` / `textContent`; if you use `innerHTML`,
escape user/model/document text with `DocMind.escapeHtml` or `renderMarkdown`.

## Visual rules (Swiss minimal, brand palette)

- Brand: Oxford Navy `#1d3557`, Cerulean `#457b9d`, Frosted Blue `#a8dadc`, Honeydew `#f1faee`, Punch Red `#e63946`.
- Use `var(--token)` only — never hard-coded hex in components. Text tokens are AAA-contrast shades (`--text`, `--text-muted`, `--link`, `--danger`). **Never put raw Cerulean or Punch Red on text**; they are for icons/borders/rings (`--icon`, `--ring`, `--secondary`, `--danger-brand`).
- Red is semantic only: errors and destructive actions.
- Sharp radii (2/4/8px), 1px borders, faint shadows; spacing from the `--s-*` scale (8px base).
- Motion: 200ms ease-out, only `transform`/`opacity`; honour `prefers-reduced-motion` (already global).
- No emojis — use `DocMind.icon()` (add new Lucide-style paths to `ICON_PATHS`). No `100vh` (use `100dvh`). No decorative gradients/noise. Plain, specific microcopy (no "seamless", "unleash", …).
- Breakpoint: collapse below 768px (sidebar becomes a drawer). Keep every page usable at 360px with no horizontal overflow.
- Every API-backed component needs loading (skeleton), empty, and error states. Labels sit above inputs; visible `:focus-visible`; real `<button>`/`<a>` elements.

## API facts to respect

- `POST /ingest/` and everything under `/documents/` and `/admin/` are admin-only; `GET /ingest/status` (document list) and `POST /query/` are for any signed-in user.
- `/query/` takes one `question` (3–1000 chars) — no conversation memory. `sources` is `[]` when the admin hides sources → render no sources UI.
- Pipeline errors return 500 with internal detail; show a friendly message, not `detail`.

## Verifying

No frontend test suite. Run the backend (`make run` in `backend/`, port 8010), then check each page in a browser: logged-out redirect, admin vs non-admin, empty/offline/error states, light + dark, 1280/768/390px, keyboard-only. A Playwright run with mocked `/api/v1/**` routes works well without touching the real database.
