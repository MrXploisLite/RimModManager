# RimModManager Wiki

## Table of Contents
- [Getting Started](#getting-started)
- [Installation Detection](#installation-detection)
- [Mod Management](#mod-management)
- [Workshop Downloads](#workshop-downloads)
- [Profiles & Backups](#profiles--backups)
- [Troubleshooting](#troubleshooting)

---

## Getting Started

### First Launch
1. Run `python main.py` or the executable
2. RimModManager auto-detects RimWorld installations
3. Select your installation from the dropdown
4. Mods are scanned and displayed

### Interface Overview
- **Mod Manager Tab**: Main mod list management
- **Workshop Tab**: Browse and download mods
- **Downloads Tab**: Monitor download progress
- **Tools Tab**: Update checker, conflict resolver

---

## Installation Detection

RimModManager detects these installation types:

| Platform | Types Detected |
|----------|----------------|
| Windows | Steam, GOG, Standalone |
| macOS | Steam, GOG, Standalone |
| Linux | Steam Native, Proton, Flatpak, Wine, Lutris, Bottles |

### Adding Custom Paths
1. Click "➕ Add Custom" button
2. Browse to your RimWorld folder
3. Select the folder containing `RimWorldWin64.exe` or `RimWorldLinux`

### Proton/Wine Detection
- Auto-detected via Wine prefix paths
- Uses **copy mode** instead of symlinks (symlinks don't work across Wine boundaries)

---

## Mod Management

### Activating Mods
- **Double-click** a mod in Available list
- **Hover** and click ➕ button
- **Drag** from Available to Active list
- **Batch**: Select multiple → click "➕ Selected"

### Deactivating Mods
- **Double-click** a mod in Active list
- **Hover** and click ➖ button
- **Drag** from Active to Available list
- **Batch**: Select multiple → click "➖ Selected"

### Load Order
- **Drag-and-drop** to reorder mods
- Use ⬆⬆/⬇⬇ buttons for top/bottom
- Use ⬆/⬇ buttons for up/down
- **Auto-Sort**: Click "🔄 Auto-Sort" to sort by dependencies

### Applying Changes
1. Arrange your mod load order
2. Click "Apply Load Order"
3. Mods are symlinked (or copied for Proton/Wine) to game folder
4. ModsConfig.xml is updated

---

## Workshop Downloads

### Requirements
- **SteamCMD** must be installed
- No Steam login required (anonymous download)

### Downloading Mods
1. Go to **Workshop** tab
2. Browse Steam Workshop in embedded browser
3. Click "Add to Queue" on mod pages
4. Click "Download All" to start

### Collection Support
- Paste collection URL
- All mods in collection are queued

### Download Location
- Default: `~/RimWorld_Workshop_Mods/`
- Configurable in Settings

---

## Profiles & Backups

### Profiles
Save different mod configurations:
1. Go to **Tools** tab → Profiles
2. Click "Save Profile"
3. Enter profile name
4. Load profiles anytime

### Backups
Auto-backup before major changes:
- Stored in config folder
- Restore from Tools → Backups

### Import/Export
- **Import from Game**: Load current ModsConfig.xml
- **Export to Game**: Write to ModsConfig.xml
- **Export as Text**: Share modlist with Workshop links

---

## Troubleshooting

### SteamCMD Not Found
Install SteamCMD:
```bash
# Arch Linux
yay -S steamcmd

# Ubuntu/Debian
sudo apt install steamcmd

# macOS
brew install steamcmd

# Windows
choco install steamcmd
```

### Mods Not Loading in Game
1. Ensure you clicked "Apply Load Order"
2. Check symlinks in game's Mods folder
3. On Windows, run as Administrator for symlink permissions

### ModsConfig.xml Issues
RimModManager writes proper format:
- Lowercase package IDs
- Correct load order (Harmony → Core → DLCs → mods)
- Proper knownExpansions (DLCs only, not Core)

### Proton/Wine Issues
- Symlinks don't work across Wine prefix
- RimModManager auto-detects and uses copy mode
- If issues persist, manually set installation type

### Performance
- Large mod collections (500+) may take time to scan
- Use search/filter to find mods quickly
- Disable unused mod source paths in Settings

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+S | Save modlist |
| Ctrl+O | Load modlist |
| Ctrl+R | Refresh mods |
| Delete | Deactivate selected |
| F5 | Rescan mods |

---

## Config Files

| Platform | Location |
|----------|----------|
| Windows | `%APPDATA%/RimModManager/` |
| macOS | `~/Library/Application Support/RimModManager/` |
| Linux | `~/.config/rimmodmanager/` |

Files:
- `config.json` - Main settings
- `modlists/*.json` - Saved modlists
- `profiles/*.json` - Mod profiles
- `backups/` - Automatic backups

---

## Reporting Bugs

- **Discord**: `romyr911`
- **GitHub Issues**: [Report here](https://github.com/MrXploisLite/RimModManager/issues)

Include:
1. OS and version
2. RimWorld installation type
3. Steps to reproduce
4. Error messages (if any)
