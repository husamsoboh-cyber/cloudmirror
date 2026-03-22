# Faza 2A: Security Review - New Endpoints & Credentials
Data: 2026-03-21
Reviewer: Claude Code terminal [security-2a]

## Summary
- Total findings: 13 (5 issues + 8 verified OK)
- Critical: 0 | High: 0 | Medium: 3 | Low: 2

---

## Findings

### [F201] settings.json creat fara permisiuni restrictive
- **Severitate:** Medium
- **Fisier:** cloudhop/settings.py:57-60
- **Problema:** `_save()` creaza fisierul temporar cu `open(tmp, "w")` care mosteneste umask-ul default (de obicei 0o644, world-readable). Dupa `os.replace()`, `settings.json` pastreaza aceleasi permisiuni. Fisierul contine parola SMTP in plaintext.
- **Attack vector:** Un alt user pe aceeasi masina (multi-user system) poate citi `~/.cloudhop/settings.json` daca fisierul are permisiuni 0o644.
- **Impact:** Expunerea credentialelor SMTP (username + password). Atacatorul poate folosi credentialele pentru a trimite email-uri in numele utilizatorului.
- **Mitigare existenta:** Directorul `_CM_DIR` este creat cu `mode=0o700`, ceea ce impiedica traversarea de catre alti useri. Aceasta ofera protectie efectiva, dar nu defense-in-depth.
- **Fix recomandat:** Seteaza explicit permisiunile pe fisierul tmp inainte de scriere:
  ```python
  fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
  with os.fdopen(fd, "w") as f:
      json.dump(settings, f, indent=2)
  ```
- **Status:** Open

---

### [F202] presets.json creat fara permisiuni restrictive
- **Severitate:** Low
- **Fisier:** cloudhop/presets.py:41-44
- **Problema:** Identic cu F201 - `_save()` foloseste `open(tmp, "w")` fara permisiuni explicite. presets.json contine config-uri de transfer (path-uri sursa/destinatie, remote names).
- **Attack vector:** Alt user pe aceeasi masina poate citi path-urile cloud si locale configurate in presets.
- **Impact:** Information disclosure - un atacator afla structura de directoare si remote-urile cloud ale utilizatorului. Mai putin sever decat F201 (nu contine credentiale).
- **Mitigare existenta:** Directorul parinte `_CM_DIR` are `mode=0o700`.
- **Fix recomandat:** Aceeasi solutie ca F201 - `os.open()` cu `mode=0o600`.
- **Status:** Open

---

### [F203] SMTP header injection prin email_from / email_to
- **Severitate:** Medium
- **Fisier:** cloudhop/email_notify.py:26-27, cloudhop/settings.py:96-99
- **Problema:** `msg["From"] = email_from` si `msg["To"] = email_to` seteaza headerele MIME fara sanitizare CRLF. Validarea din `save_settings()` (linia 98: `"@" not in val or "." not in val`) verifica doar prezenta `@` si `.`, nu respinge `\r\n`. Python MIMEText cu policy compat32 (default) NU previne injectia de headere in versiuni Python < 3.12.5.
- **Attack vector:** Utilizatorul (sau un atacator cu acces la POST /api/settings via CSRF bypass) seteaza `email_from` = `"attacker@evil.com\r\nBcc: victim@target.com"`. Aceasta trece validarea (`@` si `.` prezente). La trimitere, headerul `Bcc` este injectat in email.
- **Impact:** Trimiterea de email-uri catre destinatari neautorizati. Limitata de faptul ca SMTP envelope (`sendmail()`) este protejat in Python 3.x contra CRLF injection, deci injectia afecteaza doar headerele MIME afisate, nu rutarea efectiva SMTP.
- **Mitigare existenta:** (1) CSRF protection pe POST /api/settings. (2) Localhost-only binding. (3) Python 3.x `smtplib.sendmail()` rejecteaza CRLF in parametrii envelope.
- **Fix recomandat:** Adauga validare CRLF in `save_settings()` si in `send_email()`:
  ```python
  # In save_settings() la validarea email:
  if "\r" in val or "\n" in val:
      return {"ok": False, "msg": f"Invalid characters in {field}"}

  # In send_email() inainte de setarea headerelor:
  for field_val in (email_from, email_to, subject):
      if "\r" in field_val or "\n" in field_val:
          logger.warning("Rejected email field with CRLF: %s", field_name)
          return False
  ```
- **Status:** Open

---

### [F204] HTML injection in email body (error_messages nesanitizate)
- **Severitate:** Low
- **Fisier:** cloudhop/email_notify.py:69
- **Problema:** `error_messages` sunt inserate direct in HTML fara escaping:
  ```python
  items = "".join(f"<li ...>{msg}</li>" for msg in error_messages[:5])
  ```
  Daca un mesaj de eroare rclone contine caractere HTML (ex: un fisier numit `<img src=x onerror=alert(1)>.txt`), acestea sunt incluse raw in body-ul HTML al emailului.
- **Attack vector:** Un atacator creaza un fisier cu nume ce contine HTML/JS pe remote-ul sursa. Cand transferul esueaza pe acel fisier, mesajul de eroare rclone include path-ul. Email-ul de notificare contine HTML-ul injectat.
- **Impact:** HTML injection in email. Clientii moderni de email (Gmail, Outlook, Apple Mail) strip JavaScript din HTML emails, deci XSS efectiv nu este posibil. Ramane posibila injectia de HTML vizual (phishing inline). Impactul este foarte limitat: emailul se trimite doar catre utilizatorul proprietar.
- **Mitigare existenta:** (1) Email clients sanitizeaza JS. (2) Emailul ajunge doar la adresa configurata de user. (3) error_messages vin din rclone log parsing, nu din input direct.
- **Fix recomandat:** Escapeaza HTML in error messages:
  ```python
  from html import escape
  items = "".join(f"<li style='margin-bottom:4px;'>{escape(msg)}</li>" for msg in error_messages[:5])
  ```
- **Status:** Open

---

### [F205] test-email SMTP connection blocheaza thread-ul HTTP (30s timeout)
- **Severitate:** Medium
- **Fisier:** cloudhop/server.py:1300-1310, cloudhop/email_notify.py:31-33
- **Problema:** POST `/api/settings/test-email` apeleaza `send_email()` sincron in thread-ul request handler. `smtplib.SMTP()` are `timeout=30` (linia 31-33 in email_notify.py). Daca SMTP host-ul este un server lent sau inexistent, thread-ul HTTP este blocat pana la 30 secunde. Un utilizator care apasa "Send Test Email" de mai multe ori rapid poate bloca mai multe thread-uri simultan.
- **Attack vector:** Self-DoS: utilizatorul configureaza un SMTP host lent/invalid si apasa test de mai multe ori. Sau, in scenariul CSRF bypass: un atacator trimite multiple requests POST la test-email cu smtp_host controlat, blocand thread-urile server-ului.
- **Impact:** Server-ul HTTP devine temporar neresponsiv (max 30s per request). Nu este persistent - se recupereaza dupa timeout. Impact limitat pe o aplicatie single-user localhost.
- **Mitigare existenta:** (1) Localhost-only. (2) CSRF protection. (3) Timeout de 30s (nu indefinit). (4) ThreadingHTTPServer permite request-uri paralele.
- **Fix recomandat:** Fie (a) reduce timeout la 10s, fie (b) executa test-email intr-un thread separat cu callback, fie (c) adauga rate limiting pe endpoint-ul test-email (max 1 request la 10 secunde).
- **Status:** Open

---

## Verificari OK (fara probleme gasite)

### [F206] GET /api/settings NU expune parola - OK
- **Fisier:** cloudhop/server.py:460, cloudhop/settings.py:63-69
- **Verificare:** GET /api/settings apeleaza `load_settings()` (nu `load_settings_with_secrets()`). `load_settings()` seteaza `settings["email_password"] = ""` la linia 67 inainte de returnare.
- **Cine apeleaza `load_settings_with_secrets()`?** Doar: (1) POST /api/settings/test-email (server.py:1284) si (2) transfer completion notification (transfer.py:2513). Ambele sunt operatii interne care necesita parola reala pentru a trimite email. Nu este expusa prin GET.
- **Concluzie:** Securizat corect.

### [F207] save_settings() filtreaza la chei cunoscute - OK
- **Fisier:** cloudhop/settings.py:109-112
- **Verificare:** Linia 112: `settings = {k: merged[k] for k in defaults}` - itereaza doar peste cheile din `_default_settings()`. Orice cheie necunoscuta din input este ignorata. Un request cu `{"admin": true, "debug_mode": true}` nu poate injecta chei in settings.json.
- **Concluzie:** Filtrare robusta. Nu exista risc de key injection.

### [F208] CSRF protectie pe toate POST si DELETE routes - OK
- **Fisier:** cloudhop/server.py:476-483 (POST), cloudhop/server.py:1323-1330 (DELETE)
- **Verificare:** `do_POST()` apeleaza `_check_csrf()` la linia 482 inainte de orice route matching. `do_DELETE()` apeleaza `_check_csrf()` la linia 1329. CSRF token verification (linia 249-264) verifica token-ul din header-ul `X-CSRF-Token` contra store-ului de token-uri active cu expirare. Frontend-ul (settings.js) include header-ul `X-CSRF-Token: getCsrfToken()` in toate POST-urile (liniile 56, 81).
- **Concluzie:** CSRF protectie corecta pe toate mutating endpoints.

### [F209] Preset config validat la run time - OK
- **Fisier:** cloudhop/presets.py:98-117, cloudhop/transfer.py:2040-2050
- **Verificare:** `run_preset()` paseaza `preset["config"]` la `manager.start_transfer(config)`. `start_transfer()` valideaza: (1) source/dest non-empty (linia 2040-2041), (2) flag injection via `validate_rclone_input()` (liniile 2044-2047), (3) exclude patterns via `validate_exclude_pattern()` (liniile 2048-2050), (4) mode whitelisted la copy/sync/bisync (liniile 2065-2067), (5) bw_limit prin `validate_rclone_input()` (linia 2125).
- **Concluzie:** Chiar daca un preset este editat manual malitios in presets.json, validarea la run time previne injection. Config-ul nu este "trusted by default" - trece prin acelasi pipeline de validare ca un transfer nou.

### [F210] Preset ID validation consistenta si suficienta - OK
- **Fisier:** cloudhop/server.py:451, 1221, 1336
- **Verificare:** Toate rutele de preset valideaza ID-ul cu regex `[0-9a-f]{16}`: GET (linia 451: `re.match(r"^[0-9a-f]{16}$", preset_id)`), POST /run (linia 1221: `re.match(r"^/api/presets/[0-9a-f]{16}/run$", ...)`), DELETE (linia 1336: `re.match(r"^/api/presets/([0-9a-f]{16})$", ...)`). ID-urile sunt generate cu `secrets.token_hex(8)` = 16 hex chars (presets.py:49). Nu exista path traversal sau injection posibil cu acest charset.
- **Concluzie:** Validare consistenta, regex corect, charset restrictiv.

### [F211] Error messages din test-email sunt generice - OK
- **Fisier:** cloudhop/server.py:1314-1317
- **Verificare:** Mesajele returnate clientului sunt: `"Failed to send. Check SMTP settings."` (linia 1314) si `"Email error. Check SMTP settings."` (linia 1317). Exceptia reala este logata doar in server log (`logger.error("Test email error: %s", e)` la linia 1316), nu returnata in response. Nu se expun detalii SMTP (hostname, port, error codes) catre client.
- **Concluzie:** Information disclosure prevenita. Error messages sunt opace.

### [F212] Credentials NU apar in log-uri - OK
- **Fisier:** cloudhop/settings.py:68,76,118, cloudhop/email_notify.py:42,45
- **Verificare:** (1) settings.py logheaza doar "Settings loaded", "Settings loaded (with secrets)", "Settings saved" - fara valori. (2) email_notify.py logheaza `email_to` si `subject` (linia 42) dar nu username/password. (3) Exception logging (linia 45: `logger.exception(...)`) include stack trace-ul exceptiei SMTP, care poate contine hostname si port, dar NU credentialele (smtplib nu include parola in mesajele de eroare).
- **Concluzie:** Credentialele SMTP nu sunt logate.

### [F213] test-email ia setari din body DAR cu merge inteligent - OK
- **Fisier:** cloudhop/server.py:1284-1295
- **Verificare:** Handler-ul incarca mai intai setarile salvate (`load_settings_with_secrets()`, linia 1284), apoi suprascrie cu valorile din body doar daca sunt prezente si non-empty (linia 1294: `if key in body and body[key] != ""`). Acest pattern permite testarea cu setari noi inainte de a le salva, pastrind parola existenta daca nu se trimite una noua. Listsa de chei acceptate este hardcodata (liniile 1285-1293) la chei SMTP valide.
- **Concluzie:** Pattern corect. Nu exista risc de key injection sau de pierdere a parolei existente.

---

## Matrice de risc

| ID    | Severitate | Exploatabil remote? | Necesita CSRF bypass? | Impact |
|-------|------------|--------------------|-----------------------|--------|
| F201  | Medium     | Nu (local user)    | N/A                   | Credential leak |
| F202  | Low        | Nu (local user)    | N/A                   | Info disclosure |
| F203  | Medium     | Da (cu CSRF bypass)| Da                    | Email spoofing |
| F204  | Low        | Nu                 | N/A                   | Visual phishing in email |
| F205  | Medium     | Da (cu CSRF bypass)| Da                    | Temp DoS (30s) |

## Note
- Aplicatia ruleaza pe 127.0.0.1 only. Un atacator extern are nevoie de DNS rebinding SAU o pagina malitioasa deschisa in browser-ul utilizatorului.
- CSRF protection este corecta si efectiva pe toate endpoint-urile mutating.
- Toate findings de tip Medium au mitigari existente care reduc riscul practic. Fixurile sunt recomandate ca defense-in-depth.
- Nu s-au gasit vulnerabilitati critice sau cu high severity.
