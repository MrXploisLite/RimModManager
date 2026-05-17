# RimModManager Roadmap

## Current Version: v0.3.0

---

## Completed Features

### v0.1.0 - Foundation
- [x] Basic mod management (activate/deactivate)
- [x] Drag-and-drop load order
- [x] Symlink-based mod activation
- [x] Steam, GOG, standalone detection (Windows/macOS/Linux)
- [x] Workshop browser with embedded WebEngine
- [x] SteamCMD integration for downloads
- [x] Batch download support

### v0.2.0 - Quality of Life
- [x] Dark/Light theme toggle
- [x] Auto-update checker
- [x] Code cleanup (unused imports, variables)

### v0.2.1 - v0.2.2 - Reliability
- [x] Mod identity bug fixes (empty package_id handling)
- [x] Lowercase About.xml support
- [x] Workshop ID fallback detection
- [x] Config validation and sanitization
- [x] Import deduplication (RimPy, RimSort, plain text)
- [x] macOS GOG detection fix
- [x] UI networking resilience

### v0.2.3 - Core Hardening
- [x] Atomic writes for ModsConfig.xml (crash-safe)
- [x] SteamCMD path validation before downloads
- [x] Download retry logic (2 retries, 2s backoff)
- [x] Single-instance lock (prevent multiple app instances)
- [x] Bare except clauses replaced with specific exceptions

### v0.2.4 - Network Resilience
- [x] Retry logic for all Steam API calls
- [x] Workshop ID validation (7-12 digits, range check)
- [x] Cache corruption detection and auto-removal
- [x] Download directory write access validation
- [x] HTTP error handling (distinguish HTTP/URL/JSON errors)

### v0.2.5 - Game Detection + Fullscreen
- [x] Linux standalone detection (GOG/manual installs)
- [x] Nested folder structure support (rimworld_linux/data/noarch/game/)
- [x] Full screen toggle (F11)
- [x] Window maximized state save/restore
- [x] Reset window size option

### v0.3.0 - Big Update
- [x] **Auto-Setup Wizard** — First-run guided setup experience
- [x] **Lutris detection** — Game dirs + YAML config parsing
- [x] **Bottles detection** — Wine prefix scanning
- [x] **Heroic Games Launcher detection** — Game dirs + JSON config parsing
- [x] **Deep prefix search** — Wine/Proton prefix scanning for all launcher types
- [x] **SteamCMD auto-install** — One-click install on Linux
- [x] **Lazy Workshop Browser** — Init on first access for faster startup
- [x] **132 tests passing** — Zero feature loss verified

---

## Future Plans (v0.4.0+)

### Planned Features
- [ ] **Mod dependency auto-resolution** — Auto-download missing dependencies
- [ ] **Cloud sync** — Sync mod profiles across devices
- [ ] **Mod changelog viewer** — View mod update history
- [ ] **Performance profiler** — Identify slow mod loading
- [ ] **Mod pack presets** — Curated mod lists for common playstyles
- [ ] **Better search** — Fuzzy matching, author search, tag filtering
- [ ] **Mod rating system** — User ratings and reviews
- [ ] **Auto-backup on game launch** — Backup ModsConfig before playing
- [ ] **Mod conflict auto-resolve** — Smart suggestions for incompatible mods
- [ ] **Portable mode** — Run from USB without config in home directory

### Performance Goals
- [ ] Reduce startup time by 50%
- [ ] Memory usage under 150MB with WebEngine disabled
- [ ] Mod scanning under 2 seconds for 500+ mods
- [ ] Support 1000+ mods without UI lag

### Platform Goals
- [ ] Flatpak packaging for Linux
- [ ] Homebrew tap for macOS
- [ ] Winget package for Windows
- [ ] Better Steam Deck controller support

---

## Technical Debt
- [ ] Migrate from urllib to aiohttp for async network requests
- [ ] Add type hints to all public APIs
- [ ] Increase test coverage to 80%+
- [ ] Add integration tests for full workflows
- [ ] Document all public APIs with docstrings

---

*Last Updated: 2026-05-17*
