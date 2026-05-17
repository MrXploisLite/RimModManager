# Changelog

All notable changes to RimModManager will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
