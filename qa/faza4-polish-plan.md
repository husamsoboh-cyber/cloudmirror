# Faza 4: Polish Plan - CloudHop 0.12.0
Data: 2026-03-21
Consolidat din: Faza 1 (Code Review) + Faza 2A (Security New) + Faza 2B (Security Existing)

## Scoreboard

| Sursa | Total | Critical | High | Medium | Low | Info |
|-------|-------|----------|------|--------|-----|------|
| Faza 1 | 12 | 1 | 3 | 5 | 3 | 0 |
| Faza 2A | 5 | 0 | 0 | 3 | 2 | 0 |
| Faza 2B | 7 | 0 | 0 | 2 | 3 | 2 |
| **Total** | **24** | **1** | **3** | **10** | **8** | **2** |

## Decizie per finding

### FIX (16 findings → 5 prompturi)

| ID | Sev | Titlu | Prompt |
|----|-----|-------|--------|
| F101 | Critical | settings.js field name mismatch (SMTP broken) | A |
| F107 | Medium | save_settings boolean coercion | A |
| F203 | Medium | SMTP header injection (CRLF) | A |
| F102 | High | SMTP connection leak (try/finally) | B |
| F204 | Low | HTML injection in email body | B |
| F201 | Medium | settings.json permissions 0o600 | B |
| F202 | Low | presets.json permissions 0o600 | B |
| F103 | High | Crash backoff on successful resumes | C |
| F220 | Medium | --config in rclone flag allowlist | C |
| F221 | Medium | No subcommand validation | C |
| F112 | Medium | self.path vs path (static files query params) | D |
| F108 | Medium | Static files Cache-Control headers | D |
| F109 | Medium | Double parse_current in background_scanner | D |
| F104 | High | Race condition _parse_error_messages | D |
| F105 | Medium | Duplicate _PROVIDER_SPEEDS_MBS | E |
| F111 | Low | Dead CSRF_TOKEN parameter in render() | E |

### WON'T FIX (8 findings)

| ID | Sev | Titlu | Motiv |
|----|-----|-------|-------|
| F106 | Medium | Set truncation >50K files | Edge case extrem, >50K fisiere copiate rar |
| F110 | Low | Variable shadowing in do_POST | Code smell, zero impact (elif chain) |
| F205 | Medium | test-email blocks thread 30s | Single-user localhost, timeout exista, ThreadingHTTPServer |
| F222 | Info | setSafeHTML dead code | Dead code, nu e apelat nicaieri |
| F223 | Low | Host header case-sensitive | UX micro-issue, nu e security bypass |
| F224 | Info | Unnecessary expandvars | Home dir check e garda finala, expandvars inofensiv |
| F225 | Low | CSRF token FIFO exhaustion | Necesita attacker JS pe localhost, impact = refresh page |
| F226 | Low | Thread pool exhaustion | Single-user, CSRF required, self-DoS only |

## Prompturi de fix (5 prompturi, 3 terminale disponibile)

### Runda 1 (3 terminale in paralel)

**Prompt A: Settings & Email Validation** (3 fixes)
- F101: settings.js → email_username (3 linii in settings.js)
- F107: Boolean coercion in save_settings (5 linii in settings.py)
- F203: CRLF rejection in save_settings + send_email (6 linii in settings.py + email_notify.py)
- Fisiere atinse: settings.js, settings.py, email_notify.py
- Teste noi: 3

**Prompt B: Email Hardening + File Permissions** (3 fixes)
- F102: SMTP try/finally (restructurare email_notify.py:29-46)
- F204: html.escape pe error_messages (1 linie in email_notify.py)
- F201+F202: os.open cu 0o600 (settings.py:57-60, presets.py:41-44)
- Fisiere atinse: email_notify.py, settings.py, presets.py
- Teste noi: 2

**Prompt C: Transfer Security** (3 fixes)
- F103: Crash backoff append dupa Popen (transfer.py:1714-1751)
- F220: Remove --config din _KNOWN_RCLONE_FLAGS (transfer.py:205)
- F221: Subcommand allowlist in validate_rclone_cmd (transfer.py:235-264)
- Fisiere atinse: transfer.py
- Teste noi: 3

### Runda 2 (2 terminale in paralel)

**Prompt D: Server.py Fixes** (4 fixes)
- F112: path in loc de self.path la static (server.py:439-440)
- F108: Cache-Control: no-cache pe static (server.py:242)
- F109: Single parse_current in background_scanner (transfer.py:2486-2535)
- F104: state_lock pe _parse_error_messages (transfer.py:1186-1248)
- Fisiere atinse: server.py, transfer.py
- Teste noi: 2

**Prompt E: Cleanup** (2 fixes)
- F105: Extract _PROVIDER_SPEEDS_MBS + _estimate_duration helper (server.py)
- F111: Remove dead CSRF_TOKEN param din render() (server.py)
- Fisiere atinse: server.py
- Teste noi: 0

## Ordine executie

```
Runda 1: Prompt A + B + C  (3 terminale, paralel)
         ↓ merge + teste complete
Runda 2: Prompt D + E      (2 terminale, paralel)
         ↓ merge + teste complete
Faza 3:  UX Testing cu Playwright (pe cod fixat)
```

## Risc de conflict git

- Prompt A si B ambele ating email_notify.py → POTENTIAL CONFLICT
  Solutie: Prompt A modifica doar settings.py si settings.js.
  Prompt B modifica email_notify.py (try/finally + html.escape).
  SPLIT CLAR: A nu atinge email_notify.py pentru CRLF, doar settings.py.

- Prompt C si D ambele ating transfer.py → POTENTIAL CONFLICT
  Solutie: sunt in runde diferite (C = runda 1, D = runda 2). Fara conflict.

- Prompt D si E ambele ating server.py → POTENTIAL CONFLICT
  Solutie: sunt in runda 2 dar pe zone diferite. D: liniile 239-440. E: liniile 826-948 + 442-470.
  Conflict improbabil dar posibil. Daca apare, rezolvam manual.
