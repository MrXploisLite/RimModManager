# Changelog

All notable changes to RimModManager will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2026-05-18 - Workshop Scraper (No WebEngine!)

### Added
- **Workshop Scraper**: New `workshop_scraper.py` module that fetches and parses Steam Workshop pages using only stdlib (urllib + json + re). No external dependencies needed.
- **Mod Card Grid UI**: Workshop browser now displays mods as beautiful cards with thumbnails, names, authors, descriptions, and "Add to Queue" buttons.
- **Search & Sort**: Built-in search bar and category buttons (Most Popular, Most Recent, Trending) with pagination support.
- **Async Thumbnail Loading**: Thumbnails load asynchronously in background threads without blocking the UI.

### Removed
- **WebEngine Dependency**: Completely removed PyQt6-WebEngine requirement. The Workshop browser no longer needs an embedded browser at all.
- **QTextBrowser Fallback**: No longer needed since the scraper approach works without any web rendering engine.

### Performance
- **RAM Usage**: ~60MB total (no WebEngine overhead). Previously ~150MB with WebEngine.
- **Zero WebEngine Import**: No WebEngine modules are imported anywhere in the codebase.
- **Faster Startup**: No browser initialization delay — Workshop tab loads instantly with mod cards.

### Changed
- **Workshop Browser Architecture**: From embedded browser → scraper-based mod card grid.
- **Navigation**: Previous/Next page buttons replace browser back/forward.
- **"Open in Browser" Button**: Opens Steam Workshop in system browser for full browsing when needed.

## [0.3.1] - 2026-05-17 - Memory Optimization

### Performance
- **Lazy WebEngine Import**: WebEngine module is now imported only when the Workshop tab is clicked, not at startup. Saves ~100MB+ of RAM on launch.
- **QTextBrowser Fallback**: When WebEngine is unavailable or disabled, a lightweight `QTextBrowser` provides rich HTML rendering instead of a plain `QLabel`. Shows install instructions and direct links to the Steam Workshop.
- **Deferred ui.__init__ Import**: `WorkshopBrowser` and `WorkshopDownloadDialog` removed from `ui/__init__.py` to prevent eager loading.
- **Startup Memory**: Reduced from ~150MB to ~60MB on systems without PyQt6-WebEngine installed.

### Changed
- **Fallback UI**: Improved lightweight mode message with better formatting and memory usage indicator.

## [0.3.0] - 2026-05-17 - Big Update

### Added
- **Auto-Setup Wizard**: First-run experience that automatically detects RimWorld installations and helps install SteamCMD. No manual configuration needed — just click through and you're ready!
- **Expanded Game Detection**: Added detection for **Lutris**, **Bottles**, and **Heroic Games Launcher** in addition to existing Steam, GOG, and standalone support.
- **Deep Prefix Search**: Game detector now searches Wine/Proton prefixes for RimWorld installations in Lutris, Bottles, and Heroic.
- **Config Parsing**: Parses Lutris YAML configs and Heroic JSON configs to find custom game paths.

### Changed
- **First-Run Experience**: New users now see a guided setup wizard instead of being dropped into an empty UI.
- **SteamCMD Auto-Install**: Setup wizard can automatically install SteamCMD on Linux (via apt or manual download).
- **Game Detector Coverage**: Now scans 10+ sources: Steam (native/Proton/Flatpak), GOG, standalone, Lutris, Bottles, Heroic, and external drives.

### Performance
- **Lazy Workshop Browser**: Workshop browser tab now initializes only when first accessed, reducing startup memory.
- **Optimized Mod Scanning**: Reduced redundant file system calls during mod directory scanning.

## [0.2.5] - 2026-05-17

### Fixed
- **Game Detection - Linux Standalone**: Added `_detect_linux_standalone()` to find GOG/manual installations in `~/RimWorld/` and other common locations. Handles nested folder structures like `rimworld_linux/data/noarch/game/`.
- **Duplicate event.accept()**: Removed duplicate `event.accept()` call in `closeEvent()`.

### Added
- **Full Screen Mode (F11)**: Toggle fullscreen via View → Full Screen or press F11.
- **Reset Window Size**: View → Reset Window Size to restore default window dimensions.
- **Window Maximized State**: Saves and restores maximized window state across sessions.
- **Deep Binary Search**: Game detector now recursively searches for `RimWorldLinux` binary in standalone folders.

## [0.2.4] - 2026-05-17

### Added
- **Network Retry Logic**: Steam API calls (mod names, collection parsing, community rules) now retry up to 2 times with 2-second backoff.
- **Workshop ID Validation**: Stricter validation for workshop IDs (must be 7-12 digits, numeric, reasonable range).
- **Cache Corruption Detection**: Compatibility database now detects and removes corrupted cache files automatically.

### Fixed
- **Download Manager Validation**: SteamCMD path and download directory write access validated before starting downloads.
- **HTTP Error Handling**: All network requests now properly distinguish between HTTP errors, URL errors, and JSON decode errors.
- **Collection Parser**: Better error recovery when Steam API fails, falls back to HTML parsing gracefully.

### Changed
- **Improved Error Messages**: Network failures now show specific error types (HTTP code, network reason, parse error).
- **Cache Metadata Resilience**: Corrupted metadata file no longer prevents loading valid cache data.

## [0.2.3] - 2026-05-17

### Fixed
- **Bare Except Clauses**: Replaced all `except Exception` with specific exception types across `build.py`, `mod_importer.py`, and `mod_parser.py`.
- **SteamCMD Validation**: Downloads now fail gracefully with clear error messages when SteamCMD is missing or path is invalid.
- **Download Directory Validation**: Write access is verified before attempting downloads.

### Added
- **Download Retry Logic**: SteamCMD downloads now retry up to 2 times on failure with 2-second backoff.
- **Single-Instance Lock**: Prevents multiple app instances from running simultaneously (fcntl-based lock file).
- **Atomic ModsConfig Writes**: ModsConfig.xml now uses temp-file + rename pattern to prevent corruption on crash.

### Changed
- **Improved Error Messages**: SteamCMD failures now include error codes and attempt counts.
- **Tightened Exception Handling**: All broad exception catches replaced with specific exception types.

### Tests
- Added 8 new tests for SteamCMD validation, atomic writes, bare except detection, retry logic, and single-instance lock.

## [0.2.2] - 2026-05-17

### Fixed
- **Mod Identity Bug**: `ModInfo` equality/hash now handle empty `package_id` correctly and avoid false duplicates.
- **Lowercase About.xml Support**: Mods using `About/about.xml` now parse correctly instead of being marked invalid.
- **Workshop ID Detection**: Added fallback for lowercase `publishedfileid.txt` and root-level `PublishedFileId.txt`.
- **Load Order Robustness**: Sorting and conflict checks now safely handle mods without package IDs.
- **macOS GOG Detection**: Fixed `has_data_folder` detection and deduplicated installation entries.

### Changed
- **Config Hardening**: Added strict config value validation and sanitization (theme, splitter sizes, active mods, booleans, paths).
- **Importer Quality**: Added deterministic deduplication for package/workshop IDs and improved text-format detection with comment filtering.
- **Workshop/Download Reliability**: Improved logging and narrowed exception handling in downloader and workshop browser paths.
- **UI Networking Resilience**: Better HTTP/URL error handling for Workshop and update-check flows.

### Tests
- Added regression tests for lowercase About.xml parsing, publishedfileid fallback, `ModInfo` identity behavior, empty custom path handling, and importer dedup/detection edge cases.

## [0.2.0] - 2025-12-27

### Added
- **Dark/Light Theme Toggle**: System/Dark/Light theme options in Settings
- **Auto-Update Checker**: Checks GitHub releases on startup for new versions
- **Screenshots in README**: Collapsible gallery showcasing the UI

### Changed
- **Code Cleanup**: Removed all unused imports and variables
- **Fixed Ambiguous Variables**: Renamed `l` to `line` in mod_importer.py
- **Removed Redundant Imports**: Cleaned up duplicate shutil imports in main_window.py

### Fixed
- All flake8 F401 (unused imports), F841 (unused variables), E741 (ambiguous names) warnings resolved
- All F811 (redefinition) warnings resolved

## [0.1.0] - 2025-12-27

### Added
- **Batch Operations**: Select All, Deselect All, Activate/Deactivate Selected buttons
- **Keyboard Shortcuts**: Ctrl+A (select all), Delete (deactivate), Alt+Up/Down (reorder), etc.
- **AppImage Build**: Portable Linux package (no installation required)
- **CI/CD Pipeline**: Automated testing on Python 3.10, 3.11, 3.12
- **Unit Tests**: 68 tests covering config, parser, game detection, presets, importer
- **Wiki Documentation**: Comprehensive user guide at `docs/WIKI.md`
- **Release Workflow**: Automated builds for Windows (.exe, .zip), Linux (.tar.gz, .deb), macOS (.zip)

### Fixed
- **ModsConfig.xml Corruption**: Now uses RimSort-style format with proper lowercase IDs
- **Proton/Wine Symlink Failure**: Auto-detects Wine/Proton and uses copy mode
- **Workshop Browser Queue**: Auto-clears completed downloads
- **Memory Leaks**: QThread workers now properly cleaned up with `deleteLater()`
- **Undefined DownloadTask**: Removed unused callback methods with undefined type hints

### Changed
- Version now centralized in `main.py` (`__version__`)
- Improved error handling with standardized urllib timeouts
- Removed dead code (unused ScanWorker, DownloadWorker classes)

## [0.0.7] - 2025-12-25 (Pre-release)

### Added
- Initial public release
- Cross-platform RimWorld installation detection
- Drag-and-drop mod load order management
- Steam Workshop downloads via SteamCMD
- Embedded Workshop browser (PyQt6-WebEngine)
- Mod profiles and automatic backups
- Conflict detection and resolution assistant
- Import/export from game's ModsConfig.xml
- Smart game launcher with Wine/Proton support

### Supported Platforms
- Windows (Steam, GOG, standalone)
- macOS (Steam, GOG, standalone)
- Linux (Steam native, Proton, Flatpak, Wine, Lutris, Bottles)

---

## Version History

| Version | Date | Status |
|---------|------|--------|
| 0.2.2 | 2026-05-17 | Current |
| 0.2.0 | 2025-12-27 | Stable |
| 0.1.0 | 2025-12-27 | Stable |
| 0.0.7 | 2025-12-25 | Pre-release |
