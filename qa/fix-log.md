# Fix Log - CloudHop 0.12.0 QA

| Data | Finding | Sev | Fix | Prompt | Teste noi |
|------|---------|-----|-----|--------|-----------|
| 2026-03-21 | F101 - SMTP field mismatch | Critical | settings.js: email_smtp_username -> email_username | A | +2 |
| 2026-03-21 | F107 - Boolean coercion | Medium | settings.py: coerce string bools in save_settings | A | +1 |
| 2026-03-21 | F203 - SMTP header injection | Medium | settings.py: reject CRLF in email fields + host | A | +1 |
| 2026-03-21 | F102 - SMTP connection leak | High | email_notify.py: try/finally + CRLF sanitization | B | +1 |
| 2026-03-21 | F204 - HTML injection email | Low | email_notify.py: html.escape on error_messages | B | +1 |
| 2026-03-21 | F201 - settings.json perms | Medium | settings.py: os.open with 0o600 | B | 0 |
| 2026-03-21 | F202 - presets.json perms | Low | presets.py: os.open with 0o600 | B | 0 |
| 2026-03-21 | F103 - Crash backoff | High | transfer.py: append only on Popen failure | C | +1 |
| 2026-03-21 | F220 - --config allowlist | Medium | transfer.py: removed from _KNOWN_RCLONE_FLAGS | C | +1 |
| 2026-03-21 | F221 - Subcommand validation | Medium | transfer.py: _ALLOWED_SUBCOMMANDS allowlist | C | +3 |
| 2026-03-21 | F112 - Static files query params | Medium | server.py: path instead of self.path | D | +1 |
| 2026-03-21 | F108 - Cache-Control headers | Medium | server.py: Cache-Control: no-cache on static | D | +1 |
| 2026-03-21 | F109 - Double parse_current | Medium | transfer.py: single call, reuse status | D | 0 |
| 2026-03-21 | F104 - Race condition | High | transfer.py: local vars + state_lock | D | 0 |
| 2026-03-21 | F105 - Duplicate constant | Medium | server.py: _estimate_duration helper | E | 0 |
| 2026-03-21 | F111 - Dead CSRF param | Low | server.py: removed from render() calls | E | 0 |

## Won't Fix

| Finding | Sev | Motiv |
|---------|-----|-------|
| F106 - Set truncation >50K | Medium | Edge case extrem |
| F110 - Variable shadowing | Low | Code smell, zero impact |
| F205 - test-email 30s block | Medium | Single-user, timeout exists |
| F222 - setSafeHTML dead code | Info | Dead code, never called |
| F223 - Host case-sensitive | Low | UX only, not security |
| F224 - expandvars unnecessary | Info | Home dir check is final gate |
| F225 - CSRF FIFO exhaustion | Low | Requires attacker JS on localhost |
| F226 - Thread pool exhaustion | Low | Single-user, CSRF required |

## Stats
- Total findings: 24 (Faza 1: 12, Faza 2A: 5, Faza 2B: 7)
- Fixed: 16
- Won't fix: 8
- Teste before: 489
- Teste after: ~501
| 2026-03-22 | F305 - Version compare | Medium | server.py: semantic version comparison | Prompt G | 0 |
| 2026-03-22 | F310 - Remote validation | High | server.py: validate against rclone listremotes | Prompt G | 0 |
| 2026-03-22 | F313 - Path diacritics | High | server.py: URL decode + error message fix | Prompt G | 0 |
| 2026-03-22 | F301 - Subfolder persist | Medium | wizard.js: clear subfolder on source type change | Prompt F | 0 |
| 2026-03-22 | F307 - Multi-dest lock | Medium | wizard.js: remove button + Next enabled with valid dest | Prompt F | 0 |
| 2026-03-22 | F309 - Wizard not reset | Low | wizard.js + dashboard.js: reset state on New Transfer | Prompt F | 0 |
| 2026-03-22 | F302 - Stale file count | Medium | transfer.py: reset counters on new transfer | Prompt H | 0 |
| 2026-03-22 | F306 - Progress after resume | High | transfer.py: cumulative progress offset | Prompt H | 0 |
| 2026-03-22 | F315 - Exclude count | Medium | transfer.py: exclude filtered from total | Prompt H | 0 |
| 2026-03-22 | F321 - Keyboard tab order | Low | wizard.js: tabindex management | Prompt K | 0 |
| 2026-03-22 | F308 - Theme persist | Low | dashboard.js: localStorage for theme | Prompt I | 0 |
| 2026-03-22 | F312 - Pause/Resume buttons | Low | dashboard.js: toggle visibility by state | Prompt I | 0 |
| 2026-03-22 | F314 - Sync progress reset | Medium | dashboard.js: peak progress + verification indicator | Prompt I | 0 |
| 2026-03-22 | F322 - History link | Low | dashboard.js: fix Transfer History handler | Prompt I | 0 |
