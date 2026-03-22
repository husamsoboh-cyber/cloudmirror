# Faza 2B: Security Review - Existing Endpoints & Transfer Security

Data: 2026-03-21
Reviewer: Claude Code terminal [security-2b]
Version: 0.12.0

## Summary

- Total findings: 7
- Critical: 0 | High: 0 | Medium: 2 | Low: 3 | Informational: 2

Overall assessment: The application has a **strong security posture** for a localhost-only tool.
Input validation (validate_rclone_input, validate_rclone_cmd), CSRF protection, Host header
checks, path traversal prevention, and XSS escaping are all implemented correctly. The findings
below are defense-in-depth improvements, not exploitable vulnerabilities in the current threat model.

---

## A. Command Injection / Flag Injection

### A1. source/dest with embedded flags
**Status: OK - Safe**

`validate_rclone_input()` rejects values starting with `-` or `--`, blocking flag injection.
Since rclone is launched with `subprocess.Popen(cmd_list)` (no `shell=True`), each list element
is a separate process argument. Spaces in paths do NOT cause argument splitting.

Example: `"gdrive:path --config=/etc/passwd"` is passed as ONE argument to rclone, which treats
the entire string as a path name. The `--config` substring is NOT interpreted as a flag.

**Files verified:** `cloudhop/utils.py:133-162`, `cloudhop/transfer.py:2043-2047`, `cloudhop/transfer.py:2213`

### A2. Exclude pattern path traversal
**Status: OK - Safe**

`validate_exclude_pattern()` rejects `{`, `}`, `[`, `]` on top of `validate_rclone_input()`.
Pattern `**/../../sensitive` in excludes is NOT a security issue: excludes only REDUCE the set
of transferred files. Path traversal in an exclude pattern cannot grant access to files outside
the source. Worst case: an exclude pattern fails to match anything.

**File verified:** `cloudhop/utils.py:165-171`

### A3. bw_limit injection
**Status: OK - Safe**

`validate_rclone_input()` blocks shell metacharacters via allowlist. Input like `"10M; rm -rf /"`
fails because `;` is not in `_ALLOWED_PATTERN`. The validated value is inserted as
`--bwlimit={bw_val}` (single list element), not passed through a shell.

**Files verified:** `cloudhop/server.py:1190-1197`, `cloudhop/transfer.py:2125-2133`

### A4. configure_remote credentials
**Status: OK - Safe**

Username and password pass through `validate_rclone_input()` (rejects `-`, `--`, newlines, null
bytes, shell metacharacters). They are inserted as `f"user={username}"` / `f"pass={password}"`
which creates a SINGLE argument in the list. Passwords with `=` or spaces are safe because
`subprocess.run(cmd_list)` does not split on these characters. Rclone handles `key=value with spaces`
correctly as a single config parameter.

**File verified:** `cloudhop/transfer.py:2240-2283`

---

## B. History Resume Security

### [F220] validate_rclone_cmd allows --config flag (state file tampering)
- **Severitate:** Medium
- **Fisier:** `cloudhop/transfer.py:200-230`
- **Problema:** `--config` is in `_KNOWN_RCLONE_FLAGS` allowlist but is NEVER legitimately
  added by CloudHop to the rclone command. If an attacker modifies the state file
  (`~/.cloudhop/cloudhop_*_state.json`) to inject `--config=/path/to/evil.conf`, the
  `validate_rclone_cmd()` check on resume would PASS.
- **Attack vector:** Attacker with local filesystem write access modifies
  `~/.cloudhop/cloudhop_<id>_state.json` -> `rclone_cmd` array, adds
  `"--config=/tmp/evil.conf"` where evil.conf defines a remote pointing to
  attacker-controlled storage. User resumes the transfer via /api/history/resume.
  Rclone now reads/writes data to attacker's storage.
- **Impact:** Data exfiltration on resume. Attacker receives a copy of all transferred files.
  Requires local filesystem write access, which significantly limits the attack surface.
- **Fix recomandat:** Remove `"--config"` from `_KNOWN_RCLONE_FLAGS`. CloudHop never adds
  `--config` to commands, so it should not be in the allowlist. If rclone's default config
  path must be overridable, add it as a separate startup option, not through the command
  validation allowlist.
- **Status:** Open

### [F221] validate_rclone_cmd does not validate subcommand
- **Severitate:** Medium
- **Fisier:** `cloudhop/transfer.py:235-264`
- **Problema:** `validate_rclone_cmd()` validates the executable (must be `rclone`) and all
  `--flag` arguments (must be in allowlist), but does NOT validate the subcommand at `cmd[1]`.
  Legitimate values are `copy`, `sync`, `bisync`. But `delete`, `purge`, `deletefile`,
  `rmdir` would also pass validation since they are treated as positional arguments.
- **Attack vector:** Same as F220 -- attacker modifies state file, changes `cmd[1]` from
  `"copy"` to `"purge"`. On resume, rclone purges the destination. Or changes to `"move"`
  which deletes source files after transfer.
- **Impact:** Data destruction (purge/delete) or data loss (move deletes source). Same
  local filesystem write prerequisite as F220.
- **Fix recomandat:** Add a subcommand allowlist check in `validate_rclone_cmd()`:
  ```python
  _ALLOWED_SUBCOMMANDS = {"copy", "sync", "bisync", "check"}
  if len(cmd) > 1 and cmd[1] not in _ALLOWED_SUBCOMMANDS:
      return False
  ```
- **Status:** Open

### B5. Transfer ID and state file path traversal
**Status: OK - Safe**

Transfer ID validated with `re.match(r"^[0-9a-f]{16}$", transfer_id)` (16 hex chars only).
State file path constructed from ID, then `os.path.realpath()` check ensures it stays within
`_CM_DIR`. Double protection against path traversal.

**File verified:** `cloudhop/server.py:1231-1239`

### B6. validate_rclone_cmd allowlist completeness
**Status: OK - Adequate** (with F220 exception)

The allowlist covers all flags CloudHop actually adds to commands. Shell metacharacters
are blocked separately via `_SHELL_META`. Single-dash flags (e.g., `-v`, `-P`) are allowed
through without allowlist checking, but rclone has no dangerous single-letter flags.
The `--resync` flag (used for bisync) is intentionally NOT in the allowlist -- it's only
added during initial transfer, not saved to state (credentials are stripped). This means
bisync transfers with `--resync` cannot be resumed, which is correct behavior (--resync
should only run once).

**File verified:** `cloudhop/transfer.py:200-264`

---

## C. Path Traversal

### C6. /api/wizard/validate-path symlink bypass
**Status: OK - Safe**

Code sequence: `validate_rclone_input(path)` -> `os.path.realpath(os.path.expandvars(path))`
-> `startswith(home + os.sep)`.

1. `validate_rclone_input` blocks `$` (not in allowlist), preventing Unix env var expansion
2. `os.path.realpath` resolves ALL symlinks to final physical path
3. The resolved path must start with `home + os.sep`

Symlink attack: `/home/user/link_to_etc -> /etc` resolves to `/etc`, which fails the home
directory check. `realpath` is called BEFORE `os.path.exists`, so the check uses the
resolved path. Correct order.

**File verified:** `cloudhop/server.py:727-743`

### [F224] Unnecessary os.path.expandvars in validate-path
- **Severitate:** Informational
- **Fisier:** `cloudhop/server.py:732`
- **Problema:** `os.path.expandvars(path)` is called on the path before the home directory
  check. On Unix, `$VAR` expansion is blocked by the allowlist ($ not permitted). On Windows,
  `%VAR%` expansion IS possible because `%` is in the allowlist. Example:
  `%SYSTEMROOT%\..\..\sensitive` would expand to `C:\Windows\..\..\sensitive` -> `C:\sensitive`.
  However, `os.path.realpath` resolves this and the home directory check catches it.
- **Attack vector:** None exploitable -- the home directory check is the final gate and works
  correctly. But `expandvars` adds unnecessary attack surface.
- **Impact:** None. Defense-in-depth improvement only.
- **Fix recomandat:** Remove `os.path.expandvars()` call. The path should be used as-is after
  `realpath`. If tilde expansion is needed, `os.path.expanduser()` is safer and already implicit
  in the home directory comparison.
- **Status:** Open

### C7. /api/wizard/browse remote path traversal
**Status: OK - Safe**

Local paths (no `:` in path) are restricted to home directory with the same realpath check.
Remote paths (`gdrive:../../../`) are passed to `rclone lsjson`. Cloud providers do not have
a filesystem concept with `..` -- it is treated as a literal folder name. Rclone does not
interpret `..` for remote backends. No path traversal possible.

**File verified:** `cloudhop/server.py:756-765`

### C8. _serve_static path traversal
**Status: OK - Safe**

`filepath = os.path.realpath(os.path.join(static_dir, filename))` then checks
`filepath.startswith(os.path.realpath(static_dir) + os.sep)`. Request `/static/../server.py`
resolves to the parent directory, which does NOT start with `static_dir + os.sep`. Correctly
blocked with 403.

**File verified:** `cloudhop/server.py:226-233`

---

## D. SSRF / DNS Rebinding

### D9. Backend specifier (SSRF) bypass attempts
**Status: OK - Safe**

`validate_rclone_input()` checks `re.match(r"^:[a-zA-Z]", value)` to block on-the-fly
backend specifiers like `:http,url=http://evil.com:path`.

Bypass attempts analyzed:
- **Leading spaces:** `"  :http,url=evil"` -- passes the regex check (position 0 is space,
  not `:`). But rclone also requires `:` at position 0 for backend specifiers. Leading spaces
  make rclone treat it as a local path name. **Not exploitable.**
- **Case variation:** `:HTTP,url=...` -- regex matches `[a-zA-Z]`, covers both cases. **Blocked.**
- **Unicode tricks:** Zero-width characters before `:` -- would fail the allowlist unless they
  are in `\u0080-\uFFFF` range. Even if they pass, rclone requires ASCII `:` at byte position 0.
  **Not exploitable.**

**File verified:** `cloudhop/utils.py:151-156`

### [F223] Host header validation is case-sensitive
- **Severitate:** Low
- **Fisier:** `cloudhop/server.py:266-276`
- **Problema:** `host_name not in ("localhost", "127.0.0.1")` is a case-sensitive comparison.
  If a user navigates to `http://LOCALHOST:8787/`, the Host header would be `LOCALHOST`,
  which is not in the tuple, and the request would be rejected with 403.
- **Attack vector:** This is NOT a security bypass. DNS rebinding attacks use the attacker's
  domain (e.g., `evil.com`), not variants of "localhost". A DNS rebinding request would have
  `Host: evil.com` which is correctly rejected. The case-sensitivity only affects user
  experience if they type an unusual case in the URL bar.
- **Impact:** Minor UX issue -- users typing `LOCALHOST` or `Localhost` get 403. No security impact.
- **Fix recomandat:** Use case-insensitive comparison:
  ```python
  if host_name.lower() not in ("localhost", "127.0.0.1"):
  ```
- **Status:** Open

### D10. IPv6 loopback ([::1])
**Status: OK - Safe**

Server binds to `127.0.0.1` (IPv4 only). IPv6 requests to `[::1]` would not reach the server
at all. Even if they did, `host.split(":")[0]` on `[::1]:8787` would give `[`, which fails the
Host check. Double protection.

---

## E. XSS in Frontend

### E11. wizard.js innerHTML audit
**Status: OK - Safe**

Audited ALL 50+ `.innerHTML =` assignments in wizard.js (1781 lines). Every instance that
inserts server-derived data uses the `esc()` function, which creates a text node via
`document.createElement('div')` -> `.textContent = s` -> `.innerHTML` (proper HTML entity encoding).

Key verified patterns:
- **Folder names from /api/wizard/browse:** `esc(f.name)` at lines 1475, 1678 (text node via
  `nameText.textContent = f.name` at line 1678). **Safe.**
- **Remote names:** Built from client-side `providerIcons` map + `item.display` (line 744-760).
  Display names come from hardcoded provider map. **Safe.**
- **Error messages:** `esc(data.msg || '...')` at lines 703, 1155, 1184, 1481, 1685. **Safe.**
- **Source/dest paths in summary card:** `esc(srcDisplay)`, `esc(dstDisplay)` at lines 979-1007.
  **Safe.**
- **Static HTML strings** (spinners, checkmarks, hints): No server data. **Safe.**

**File verified:** `cloudhop/static/wizard.js` (full file)

### E12. dashboard.js innerHTML audit
**Status: OK - Safe** (with one informational note)

Audited ALL 40+ `.innerHTML =` assignments in dashboard.js (1719 lines). Server data is
consistently escaped with `esc()`.

Key verified patterns:
- **Active transfer filenames:** `esc(t.name)`, `esc(t.size)`, `esc(eta)` at lines 868-882. **Safe.**
- **Error messages:** `esc(friendly)` at line 788-790. **Safe.**
- **Recent files:** `esc(f.name)`, `esc(ext)`, `esc(f.time)` at lines 892-897. **Safe.**
- **File types:** `esc(ext)` at line 916. **Safe.**
- **Session timeline:** `esc(s.start)`, `esc(s.end)`, `esc(s.transferred)`, `esc(s.elapsed)`,
  `esc(dt.duration)` at lines 822-836. **Safe.**
- **Queue list:** `esc(cfg.source)`, `esc(cfg.dest)`, `esc(status)`, `esc(qid)`, `esc(addedAt)`
  at lines 1621-1640. **Safe.**
- **Preset list:** `esc(p.name)`, `esc(srcLabel)`, `esc(dstLabel)`, `esc(mode)`, `esc(lastUsed)`
  at lines 1701-1718. **Safe.**
- **Speed indicator:** `Math.abs(diff).toFixed(2)` -- numeric only (line 714). **Safe.**
- **Completion overlay:** Uses `.toLocaleString()` for file count and server-formatted strings
  for size/time (line 366). Data comes from rclone status parsing (trusted internal source).
  **Acceptable risk.**

### [F222] setSafeHTML regex sanitizer is weak (dead code)
- **Severitate:** Informational
- **Fisier:** `cloudhop/static/dashboard.js:324-332`
- **Problema:** The `setSafeHTML()` function uses regex-based sanitization that strips
  `<script>` tags and replaces `onXXX=` event handlers. This approach is bypassable:
  - `<a href="javascript:alert(1)">click</a>` -- passes through (no script tag, no onXXX)
  - `<iframe src="javascript:alert(1)">` -- passes through
  - `<details open ontoggle=alert(1)>` -- `ontoggle=` IS caught by regex, safe
- **Attack vector:** None currently. `setSafeHTML()` is defined but **never called** anywhere
  in dashboard.js or wizard.js. It is dead code.
- **Impact:** None. But if a future developer uses it thinking it provides XSS protection,
  they would be vulnerable.
- **Fix recomandat:** Either remove the dead function or replace with proper sanitization
  (DOMPurify, or use `textContent` instead of `innerHTML` for untrusted data). Add a
  code comment warning that regex-based HTML sanitization is insufficient.
- **Status:** Open

---

## F. CSRF Completeness

### F13. CSRF on all mutating endpoints
**Status: OK - Complete**

Verified that all mutating HTTP methods call `_check_csrf()` as the first check after
`_check_host()`:
- `do_POST()`: `_check_csrf()` at line 482. All POST routes below this point are protected. **OK.**
- `do_DELETE()`: `_check_csrf()` at line 1329. **OK.**
- `do_PUT()`: `_check_csrf()` at line 1365. **OK.**
- `do_GET()`: Does not need CSRF (read-only). **OK.**
- `do_OPTIONS()`: Does not need CSRF (CORS preflight). **OK.**

No bypass paths exist. The CSRF check is at the method handler level, not per-route,
so it is impossible to add a new POST route without CSRF protection (unless the check
is explicitly removed).

CSRF token validation uses `_csrf_tokens` dict lookup (not `hmac.compare_digest` for lookup,
but the token is a 256-bit random value from `secrets.token_hex(32)`, making brute-force
infeasible). Token expiry is 24 hours. Cookie is `SameSite=Strict`.

**File verified:** `cloudhop/server.py:249-264, 476-483, 1323-1330, 1359-1366`

### [F225] CSRF token store FIFO exhaustion
- **Severitate:** Low
- **Fisier:** `cloudhop/server.py:87-101`
- **Problema:** `_MAX_CSRF_TOKENS = 100`. When the limit is reached, the oldest token is
  evicted (FIFO). An attacker who can make requests to localhost could request 100 page
  loads (each generates a new token via `_send_html`), evicting the user's legitimate token.
  The user's next POST request would fail CSRF validation.
- **Attack vector:** Attacker has JS running in another browser tab on the same machine.
  Sends 100 GET requests to `/wizard` or `/dashboard` (no CSRF needed for GET). Each
  generates a new token. User's original token gets evicted. User's next action fails.
- **Impact:** Denial of service for CSRF-protected actions. User must refresh the page to
  get a new token. This is a minor annoyance, not a security bypass. The attacker cannot
  perform actions -- they can only prevent the user from performing actions.
- **Fix recomandat:** Increase `_MAX_CSRF_TOKENS` to 1000, or use a per-session token
  model (one long-lived token per session instead of per-page-load). Alternatively,
  rate-limit page loads from the same IP (though all traffic is localhost).
- **Status:** Open

---

## G. Denial of Service

### [F226] Thread pool exhaustion via long-running endpoints
- **Severitate:** Low
- **Fisier:** `cloudhop/server.py:789-888` (preview), `cloudhop/server.py:766-788` (browse)
- **Problema:** `ThreadingHTTPServer` creates one thread per request. The `/api/wizard/preview`
  endpoint has a 60s timeout (`RCLONE_PREVIEW_TIMEOUT_SEC`) and `/api/wizard/browse` has 30s.
  Python's `ThreadingHTTPServer` has no built-in thread limit. An attacker sending concurrent
  requests could spawn many threads, each blocking for up to 60s on `subprocess.run()`.
- **Attack vector:** Malicious JS in another browser tab sends 50+ concurrent POST requests to
  `/api/wizard/preview` with a valid CSRF token (obtained via page load). Each request spawns
  an rclone process that runs for up to 60s. The server's thread pool grows unbounded.
- **Impact:** Resource exhaustion on the local machine (CPU/memory from 50+ rclone processes +
  50+ Python threads). Server becomes unresponsive. Requires localhost access and a valid
  CSRF token (obtainable from a page load in the same browser).
- **Fix recomandat:** Add a concurrent request limit for long-running endpoints using a
  `threading.Semaphore`. Example:
  ```python
  _preview_semaphore = threading.Semaphore(3)  # max 3 concurrent previews
  if not _preview_semaphore.acquire(blocking=False):
      return {"ok": False, "msg": "Too many concurrent requests"}
  ```
- **Status:** Open

### G17. 10KB body limit enforcement
**Status: OK - Universally Applied**

`_read_body()` enforces `MAX_REQUEST_BODY_BYTES = 10240` for all POST handlers that read
request bodies. Endpoints that don't read the body (`/api/pause`, `/api/resume`, `/api/verify`,
`/api/wizard/check-rclone`, `/api/wizard/install-rclone`) don't need the limit because they
don't process body data. Unread body data in the TCP buffer does not affect these handlers.

**File verified:** `cloudhop/server.py:278-296`

---

## Verification Summary

| Check Point | Result | Notes |
|---|---|---|
| A1. Source/dest flag injection | **SAFE** | List args + validate_rclone_input |
| A2. Exclude path traversal | **SAFE** | Excludes only reduce file set |
| A3. bw_limit injection | **SAFE** | Allowlist blocks shell metacharacters |
| A4. configure_remote credentials | **SAFE** | List args + newline blocking |
| B5. History resume ID/path | **SAFE** | Hex-16 regex + realpath check |
| B6. validate_rclone_cmd flags | **F220** | --config should not be in allowlist |
| B7. Subcommand validation | **F221** | No check on cmd[1] |
| C6. validate-path symlink | **SAFE** | realpath resolves before check |
| C7. browse remote paths | **SAFE** | Cloud providers ignore .. |
| C8. _serve_static traversal | **SAFE** | realpath + startswith check |
| D9. SSRF backend specifier | **SAFE** | Regex + allowlist + rclone behavior |
| D10. Host header validation | **F223** | Case-sensitive (low impact) |
| D11. IPv6 loopback | **SAFE** | Server binds IPv4 only |
| E11. wizard.js XSS | **SAFE** | All server data uses esc() |
| E12. dashboard.js XSS | **SAFE** | All server data uses esc() |
| E13. setSafeHTML | **F222** | Dead code, weak sanitizer |
| F13. CSRF completeness | **SAFE** | All POST/DELETE/PUT protected |
| F14. CSRF token exhaustion | **F225** | FIFO eviction at 100 tokens |
| G15-16. Thread exhaustion | **F226** | No concurrent request limit |
| G17. Body size limit | **SAFE** | 10KB universally enforced |
| C9. expandvars | **F224** | Unnecessary, adds attack surface |

---

## Risk Assessment

All findings require **local access** to exploit (either filesystem write access for state file
tampering, or the ability to run JavaScript in the user's browser on localhost). The application's
primary security boundary -- binding to 127.0.0.1 with Host header validation -- is solid and
effectively prevents remote attacks.

The most actionable fixes are **F220** (remove `--config` from allowlist) and **F221** (add
subcommand validation), which are simple one-line changes that close a defense-in-depth gap.
