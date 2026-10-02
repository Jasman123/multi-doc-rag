---
name: design-md-planner
description: Plan a frontend page, feature, or redesign by writing a DESIGN.md spec (goals, users, layout, components, states, tokens, API wiring, build steps) before any code is written. Use when the user wants to design, redesign, or plan UI in frontend/, or says "design md", "plan the design", or "design spec".
---

# Design MD planner

Produce a `DESIGN.md` that is detailed enough to implement from, and get the user's approval on
it **before writing any frontend code**. This skill plans; it does not build. Implementation
conventions live in the `frontend-design` skill — follow them when filling in the spec.

## Process

1. **Ground in the repo.** Read the relevant existing pages in `frontend/` (and the `:root` tokens
   in `index.html`) and the API routes the design will call (`backend/app/`). Note what can be reused.
   Do not ask the user things the code already answers.
2. **Clarify only what's missing.** If the request leaves open the target page(s), the primary user
   action, or the desired look/feel, ask in one batch (max 3–4 questions, with a recommended default
   for each). If the request is clear enough, skip questions and state your assumptions in the doc.
3. **Write the spec** to `docs/design/<slug>/DESIGN.md` (kebab-case slug of the feature, e.g.
   `docs/design/documents-redesign/DESIGN.md`). Create the folder. If a `DESIGN.md` already exists
   there, update it rather than starting over.
4. **Hand over for review.** Summarise in a few lines: the key design decisions, open questions, and
   assumptions. Ask the user to approve or redirect. Do not start implementing until they say so.

## DESIGN.md template

Keep every section short and concrete; delete a section only if it truly doesn't apply.

```markdown
# <Feature / page name> — Design

Status: Draft | Approved   ·   Branch: <git branch>   ·   Date: <YYYY-MM-DD>

## 1. Goal
One or two sentences: what the user can do after this ships, and why it matters.

## 2. Users and key tasks
Who uses it (regular user vs admin) and the 2–4 tasks it must make easy. Mark the primary task.

## 3. Scope
- In scope:
- Out of scope / later:

## 4. Pages and navigation
Which files in `frontend/` are new or changed, how users arrive and leave (redirects, nav links).

## 5. Layout
ASCII wireframe per page/breakpoint (desktop first, then narrow/mobile). Name each region.

## 6. Components
Table: component · purpose · states · reuses existing? (file/class). Include empty, loading,
error, and success states for anything backed by an API call.

## 7. Visual language
Tokens used (`var(--…)` from the existing `:root`), any NEW tokens with values and justification,
typography roles (heading / body / mono), spacing, motion. Prefer reuse over invention.

## 8. Data and API wiring
Table: UI action · endpoint · method · request/response fields used · auth/role required.
Flag any endpoint that doesn't exist yet (needs backend work — call that out separately).

## 9. Behaviour and edge cases
Auth redirects, token refresh, validation messages, long text, large lists, permissions,
keyboard/focus, accessibility (contrast, labels, focus rings), responsive behaviour.

## 10. Implementation plan
Ordered, small steps, each independently verifiable (e.g. "1. Add static markup + CSS for the
list; 2. Wire GET /documents/; 3. Delete flow with confirm"). Note duplicated code that must be
changed in several pages.

## 11. Verification
How to confirm it works: run the app, the pages/flows to click through, and the edge cases from §9.
There is no frontend test suite — say which manual checks stand in for tests.

## 12. Open questions and risks
Decisions the user still owns, and anything that could change the plan.
```

## Rules

- Be specific: real class/token names, real endpoint paths, real filenames. No generic filler.
- Don't invent endpoints or fields — verify them in `backend/app/`, or list them as "needs backend".
- No new frameworks, build tooling, or CDN dependencies in the plan unless the user asked for them.
- Use fictitious/placeholder data in wireframes and copy; never real client names or personal data.
- Keep the doc scannable: tables and short bullets over prose. Aim for a spec a teammate can read in
  five minutes.
- After approval, set `Status: Approved`, then implement step by step per §10 (following the
  `frontend-design` skill), updating the doc if the plan changes.
