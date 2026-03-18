# Changelog

All notable changes to CloudMirror are documented here.

## v0.3.0 (2026-03-19)

### Added
- Progress percentage in browser tab title (`[45%] CloudMirror`)
- Bandwidth limit option in wizard (e.g. 10M, 1G, 500K)
- Dry-run / Preview button on summary step (shows file count and size before starting)
- Transfer history API (`/api/history`) with link in dashboard footer
- Smoothed ETA calculation based on average speed (less fluctuation)
- Error message mapping (translates rclone errors to user-friendly messages)
- OAuth reconnect hint when token-related errors appear
- Chart cache invalidation on theme toggle (charts redraw with correct colors)

## v0.2.0 (2026-03-18)

### Added
- OAuth hint conditional (different message for browser auth vs credentials)
- Rclone installation check on Welcome page (warns before user proceeds)
- Wizard state persistence via sessionStorage (survives page refresh)
- Cancel Transfer button on dashboard (with confirmation dialog)
- Dead process detection (badge shows "Stopped" in red when rclone dies)
- Quick-select buttons for local folder paths (Desktop, Documents, Downloads)
- Auto-create destination folder if it doesn't exist

### Fixed
- Proton/MEGA/S3 credentials now save correctly (key=value format)
- Proton Drive label no longer shows as "Google Drive"
- Quick-select buttons use actual home directory (not localhost fallback)
- Quick-select buttons meet 44px touch target on mobile
- Zombie rclone size processes prevented (only one at a time)
- Dead rclone process properly detected (waitpid instead of kill)
- Empty local path shows alert instead of defaulting to "/" (read-only)

## v0.1.0 (2026-03-18)

### Features
- Web-based 6-step setup wizard with provider selection
- Real-time transfer dashboard with live-updating charts
- Supports Google Drive, OneDrive, Dropbox, MEGA, Amazon S3, Proton Drive, Local Folder
- Dark/light theme toggle with persistence
- Pause/Resume/Cancel transfers
- Session history tracking with downtime detection
- Speed, progress, and file count history charts
- Active transfer list and recent files feed
- File type breakdown
- Error tracking and display
- CLI mode for direct rclone argument passthrough
- Automatic rclone installation (macOS and Linux)
- Sound and desktop notification on transfer completion
- Single Python file, no dependencies beyond Python 3.7+

### Security
- Web server binds to localhost only (127.0.0.1)
- CORS restricted to localhost origins (strict set comparison)
- Input validation prevents rclone flag injection
- Request body size limited to 10 KB
- Credentials obscured before saving
- State files stored in ~/.cloudmirror/ with 0700 permissions

### Accessibility
- Provider cards keyboard-accessible (tabindex, role, onkeydown)
- Form labels linked to inputs
- Theme toggle and all buttons meet 44px minimum touch target
- Mobile responsive (375px to 1280px)
