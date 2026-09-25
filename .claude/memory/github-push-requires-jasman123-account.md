---
name: github-push-requires-jasman123-account
description: "Pushing to Jasman123-owned repos needs the Jasman123 gh account active, not jasmanjasman"
metadata:
  type: project
---

This machine has two GitHub accounts logged into `gh`: `jasmanjasman` and `Jasman123` (owner of
this repo). Only `Jasman123` has write access — pushing while `jasmanjasman` is the active account
fails with `remote: Permission ... denied to jasmanjasman` / HTTP 403.

Fix: `gh auth switch --hostname github.com --user Jasman123`. The active account is global, not
per-repo, so switch back if pushes to other (non-Jasman123) repos start failing.

Pinning the owner in the remote URL does **not** work: gh's credential helper only serves the
active account, so git falls through to a password prompt.

**Why:** the 403 looks like a repo-permissions problem but is actually an account-selection one.

**How to apply:** on any 403 push from this repo, check `gh auth status` for which account is
active before touching remotes or tokens.
