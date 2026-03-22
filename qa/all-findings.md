# CloudHop 0.12.0 - All Findings Master List
Ultima actualizare: 2026-03-22
Surse: Faza 1, Faza 2A, Faza 2B, Faza 3, Faza 3B, Faza 3C, Faza 3D

## Scoreboard

| Status | Count |
|--------|-------|
| FIXED | 30 |
| OPEN (to fix) | 0 |
| DEFERRED | 3 |
| WON'T FIX | 8 |
| FALSE POSITIVE | 1 |
| **TOTAL** | **42** |

Teste: 501 passed, 3 skipped | CI: all green
PRs: #1 (server), #2 (wizard), #3 (transfer), #4 (wizard a11y), #5 (dashboard) — all merged

---

## FIXED (30)

### Faza 1-2 Fixes (16) — Prompt A-E

| ID | Sev | Titlu | Fix |
|----|-----|-------|-----|
| F101 | Critical | settings.js field name mismatch (SMTP broken) | email_smtp_username → email_username |
| F102 | High | SMTP connection leak | try/finally in email_notify.py |
| F103 | High | Crash backoff penalizeaza resume-uri | append doar la Popen failure |
| F104 | High | Race condition _parse_error_messages | local vars + state_lock |
| F105 | Medium | _PROVIDER_SPEEDS_MBS duplicat | _estimate_duration helper |
| F107 | Medium | save_settings boolean coercion | coerce string bools |
| F108 | Medium | Static files fara Cache-Control | Cache-Control: no-cache |
| F109 | Medium | Double parse_current in scanner | single call, reuse status |
| F111 | Low | Dead CSRF_TOKEN param in render() | removed from render() |
| F112 | Medium | self.path vs path static files | path instead of self.path |
| F201 | Medium | settings.json fara 0o600 perms | os.open cu 0o600 |
| F202 | Low | presets.json fara 0o600 perms | os.open cu 0o600 |
| F203 | Medium | SMTP header injection CRLF | reject \r\n in email fields |
| F204 | Low | HTML injection in email body | html.escape on error_messages |
| F220 | Medium | --config in rclone flag allowlist | removed from _KNOWN_RCLONE_FLAGS |
| F221 | Medium | No subcommand validation | _ALLOWED_SUBCOMMANDS allowlist |

### Faza 3 Fixes — Round 1: PR #1, #2, #3

| ID | Sev | Titlu | Fix | PR |
|----|-----|-------|-----|----|
| F301 | Medium | Source subfolder persista cand schimbi sursa | wizard.js: clear subfolder in selectSource() | #2 |
| F302 | Medium | Contor total fisiere stale | transfer.py: _default_state() in set_transfer_paths() | #3 |
| F305 | Medium | Update banner zice downgrade e upgrade | server.py: semantic tuple version comparison | #1 |
| F306 | High | Progress bar reset dupa Resume | transfer.py: _resume_bytes_offset + max() floor | #3 |
| F307 | Medium | Multi-dest "+Add" blocheaza wizard | wizard.js: Next enabled when multiDestinations.length > 0 | #2 |
| F309 | Low | "New Transfer" nu reseteaza wizard | wizard.js: ?new=1 param + clear sessionStorage | #2 |
| F310 | High | Remote inexistent acceptat fara validare | server.py: validate against rclone listremotes | #1 |
| F313 | High | Path validation 403 pt diacritice | server.py: urllib.parse.unquote + clear error messages | #1 |
| F315 | Medium | Exclude folders: total include excluse | transfer.py: include user excludes in _fetch_source_size() | #3 |

### Faza 3 Fixes — Round 2: PR #4, #5

| ID | Sev | Titlu | Fix | PR |
|----|-----|-------|-----|----|
| F308 | Low | Theme toggle nu persista | dashboard.js: localStorage save/load for theme | #5 |
| F312 | Low | Pause si Resume vizibile simultan | dashboard.js: updateButtons() in error+running branch | #5 |
| F314 | Medium | Sync progress resets in verificare | dashboard.js: peakProgressPct + "Verifying..." indicator | #5 |
| F321 | Low | Keyboard nav 20+ Tab per step | wizard.js: _updateProviderTabOrder() + auto-focus | #4 |
| F322 | Low | Transfer History link "#" | dashboard.js: addEventListener + javascript:void(0) | #5 |

## FALSE POSITIVE (1)

| ID | Sev | Sursa | Titlu | Motiv |
|----|-----|-------|-------|-------|
| F320 | Medium | Faza 3D | CSRF token nevalidat | Already implemented: _csrf_tokens dict + _check_csrf() + X-CSRF-Token header. Commits 1d09fad, 76633b9. Tester tampered cookie but server validates against server-side store. |

## DEFERRED (3)

| ID | Sev | Sursa | Titlu | Motiv |
|----|-----|-------|-------|-------|
| F304 | Medium | Faza 3 | Copy la cloud root nu creeaza folder wrapper | Comportament rclone standard |
| F311 | Medium | Faza 3B | Proton Drive: erori + viteza mica | Comportament rclone + Proton API |
| F322-enh | Low | Faza 3D | No delete/clear pt completed transfers | Feature request, not bug |

## WON'T FIX (8)

| ID | Sev | Sursa | Titlu | Motiv |
|----|-----|-------|-------|-------|
| F106 | Medium | Faza 1 | Set truncation >50K files | Edge case extrem |
| F110 | Low | Faza 1 | Variable shadowing do_POST | Zero impact |
| F205 | Medium | Faza 2A | test-email blocks thread 30s | Single-user, timeout exists |
| F222 | Info | Faza 2B | setSafeHTML dead code | Never called |
| F223 | Low | Faza 2B | Host header case-sensitive | UX only |
| F224 | Info | Faza 2B | Unnecessary expandvars | Inofensiv |
| F225 | Low | Faza 2B | CSRF token FIFO exhaustion | Requires attacker JS on localhost |
| F226 | Low | Faza 2B | Thread pool exhaustion | Single-user, CSRF required |
| F303 | Low | Faza 3 | Wizard nu suporta fisier individual | Feature request |

## Faze completate

| Faza | Status | Findings | Fixed |
|------|--------|----------|-------|
| Faza 1 - Code Review | DONE | 12 | 10 |
| Faza 2A - Security (new endpoints) | DONE | 5 | 4 |
| Faza 2B - Security (existing endpoints) | DONE | 7 | 2 |
| Faza 3 - UX Testing (basic) | DONE | 5 | 4 |
| Faza 3B - UX Testing (advanced) | DONE | 8 | 6 |
| Faza 3C - UX Testing (edge cases) | DONE | 4 | 3 |
| Faza 3D - UX Testing (resilience) | DONE | 3 | 1 |
| **TOTAL** | **DONE** | **42** | **30** |

## Git History (PRs)

| PR | Branch | Fixes | Merged |
|----|--------|-------|--------|
| #1 | fix/server-validation | F305, F310, F313 | 2026-03-22 |
| #2 | fix/wizard-state | F301, F307, F309 | 2026-03-22 |
| #3 | fix/transfer-progress | F302, F306, F315 | 2026-03-22 |
| #4 | fix/wizard-a11y | F321 | 2026-03-22 |
| #5 | fix/dashboard-ui | F308, F312, F314, F322 | 2026-03-22 |

## Fisiere QA

```
/tmp/cloudhop-fix/qa/
├── all-findings.md
├── faza1-code-review.md
├── faza2a-security-new-endpoints.md
├── faza2b-security-existing.md
├── faza3-ux-testing.md
├── faza3b-ux-testing-advanced.md
├── faza3c-ux-testing-edge.md
├── faza3d-ux-testing-resilience.md
├── faza4-polish-plan.md
├── fix-log.md
├── faza3-screenshots/
├── faza3b-screenshots/
├── faza3c-screenshots/
├── faza3d-screenshots/
└── faza3-logs/
```
