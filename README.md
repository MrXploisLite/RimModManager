# RimModManager

<div align="center">

**The Ultimate Cross-Platform Mod Manager for RimWorld**

[![Release](https://img.shields.io/github/v/release/MrXploisLite/RimModManager?style=flat-square&include_prereleases)](https://github.com/MrXploisLite/RimModManager/releases)
[![GitHub license](https://img.shields.io/github/license/MrXploisLite/RimModManager?style=flat-square)](https://github.com/MrXploisLite/RimModManager/blob/main/LICENSE)
[![GitHub issues](https://img.shields.io/github/issues/MrXploisLite/RimModManager?style=flat-square)](https://github.com/MrXploisLite/RimModManager/issues)
[![GitHub stars](https://img.shields.io/github/stars/MrXploisLite/RimModManager?style=flat-square)](https://github.com/MrXploisLite/RimModManager/stargazers)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg?style=flat-square)](https://www.python.org/downloads/)
[![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green.svg?style=flat-square)](https://www.riverbankcomputing.com/software/pyqt/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey?style=flat-square)](https://github.com/MrXploisLite/RimModManager)

[Features](#-features) • [Download](#-download) • [Installation](#-installation) • [Wiki](docs/WIKI.md) • [Contributing](#contributing)

</div>

---

## 🎯 Why RimModManager?

Managing 200+ RimWorld mods shouldn't be painful. RimModManager is a **free, open-source** mod manager that works on **any platform** and supports **any installation type** - Steam, GOG, Proton, Wine, Flatpak, or standalone.

- ✅ **No Steam required** - Works with cracked/standalone versions
- ✅ **Non-destructive** - Uses symlinks, never modifies your mods
- ✅ **Cross-platform** - Windows, macOS, Linux (including Steam Deck!)
- ✅ **Workshop downloads** - Download mods without owning the game on Steam
- ✅ **Conflict detection** - Know which mods break each other

---

## 📸 Screenshots

<details>
<summary><b>Click to view screenshots</b></summary>

### Mod Manager
![Mod List](Screenshots/image-mods-list.png)

### Workshop Browser
![Workshop](Screenshots/image-workshop+mods.png)

### Downloads
![Downloads](Screenshots/image-mods-downloads.png)

### Game Launcher
![Launcher](Screenshots/image-launchgame.png)

### Keyboard Shortcuts
![Shortcuts](Screenshots/image-KeyboardShortcuts.png)

</details>

---

## 📥 Download

**[⬇️ Download Latest Release (v0.5.2)](https://github.com/MrXploisLite/RimModManager/releases/tag/v0.5.2)**

| Platform | File | Notes |
|----------|------|-------|
| 🐧 Linux | `RimModManager-Linux-x64` | `chmod +x && ./RimModManager-Linux-x64` |
| 🪟 Windows | `RimModManager-Windows-x64.exe` | Double-click to run |
| 🍎 macOS | `RimModManager-macOS-x64` | `chmod +x && ./RimModManager-macOS-x64` |

> Binaries are built automatically via GitHub Actions on each release.

### Quick Start (Linux)
```bash
# Download from releases page
chmod +x RimModManager-Linux-x64
./RimModManager-Linux-x64
```

### Or Run from Source
```bash
git clone https://github.com/MrXploisLite/RimModManager.git
cd RimModManager
pip install PyQt6
python main.py
```

### Build Your Own
```bash
pip install PyQt6 PyInstaller
python build.py
```

---

## ✨ Features

<table>
<tr>
<td width="50%">

### 🎮 Universal Game Detection
- **Windows**: Steam, GOG, standalone
- **macOS**: Steam, GOG, standalone  
- **Linux**: Steam native, Proton, Flatpak, Wine, Lutris, Bottles, Heroic, standalone
- **Auto-Setup Wizard**: First-run guided setup — zero manual config needed

### 📦 Mod Management
- Drag-and-drop load order
- Symlink-based activation (non-destructive)
- Hover buttons (➕/➖) for quick toggle
- Search and filter mods
- Auto-sort by dependencies
- Uninstall mods safely

</td>
<td width="50%">

### 🔧 Workshop Integration
- Embedded Steam Workshop browser
- One-click download queue
- Parse entire Collections
- Batch downloads (single SteamCMD session)
- Check for mod updates
- View subscriber counts & ratings

### 📋 Profiles & Backups
- Save/load mod profiles
- Auto-backup before changes
- Import/export ModsConfig.xml
- Per-installation mod lists

</td>
</tr>
</table>

### 🛠️ Advanced Tools
| Tool | Description |
|------|-------------|
| **Update Checker** | Compare local mods vs Workshop versions |
| **Conflict Resolver** | Detect conflicts with fix suggestions |
| **Enhanced Info** | View Workshop stats (subs, favs, views) |
| **Smart Launcher** | Auto-detects Steam vs standalone |
| **Lightweight Mode** | Use system browser to save 100MB+ RAM |

---

## 🔨 Build from Source

You can build a standalone executable that doesn't require Python to run.

1. **Install Requirements**
   ```bash
   pip install pyinstaller
   ```

2. **Build**
   ```bash
   python build.py
   ```

3. **Result**
   The executable will be in the `dist/` folder.
   - **Size**: ~60-70MB (Lightweight)
   - **Compression**: Automatically uses UPX if installed
   - **Portable**: No installation required

---

## 🚀 Installation

### Requirements
- Python **3.10+**
- `PyQt6` (required)
- `PyQt6-WebEngine` (optional, only for embedded Workshop browser)
- `steamcmd` (optional, only for Workshop downloads)

### Quick Start
```bash
git clone https://github.com/MrXploisLite/RimModManager.git
cd RimModManager
python -m pip install PyQt6
# Optional for embedded Workshop browser:
# python -m pip install PyQt6-WebEngine
python main.py
```

<details>
<summary><b>📦 Windows Installation</b></summary>

```powershell
# Install Python from https://python.org
python -m pip install PyQt6
# Optional for embedded Workshop browser:
# python -m pip install PyQt6-WebEngine

# SteamCMD (for Workshop downloads)
# Option 1: Download from https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip
# Option 2: choco install steamcmd
```
</details>

<details>
<summary><b>🍎 macOS Installation</b></summary>

```bash
python -m pip install PyQt6
# Optional for embedded Workshop browser:
# python -m pip install PyQt6-WebEngine
brew install steamcmd
```
</details>

<details>
<summary><b>🐧 Linux Installation</b></summary>

**Arch / CachyOS / EndeavourOS / Manjaro:**
```bash
sudo pacman -S python python-pyqt6
# Optional for embedded Workshop browser:
# sudo pacman -S python-pyqt6-webengine
yay -S steamcmd
```

**Ubuntu / Debian:**
```bash
python -m pip install PyQt6
# Optional for embedded Workshop browser:
# python -m pip install PyQt6-WebEngine
sudo apt install steamcmd
```

**Fedora:**
```bash
python -m pip install PyQt6
# Optional for embedded Workshop browser:
# python -m pip install PyQt6-WebEngine
sudo dnf install steamcmd
```
</details>

<details>
<summary><b>🎮 Steam Deck Installation</b></summary>

```bash
# Switch to Desktop Mode
# Open Konsole and run:
python -m pip install --user PyQt6
# Optional for embedded Workshop browser:
# python -m pip install --user PyQt6-WebEngine
git clone https://github.com/MrXploisLite/RimModManager.git
cd RimModManager
python main.py
```
</details>

---

## 📖 Usage

### First Launch
1. Run `python main.py` or the executable
2. The **Auto-Setup Wizard** guides you through setup
3. RimWorld installations are auto-detected
4. SteamCMD is auto-installed if needed

###日常管理
1. **Select** your RimWorld installation from dropdown
2. **Manage** mods with drag-and-drop or hover buttons
3. **Apply** changes with "Apply Load Order"
4. **Play** with the built-in launcher

### Config Locations
| Platform | Path |
|----------|------|
| Windows | `%APPDATA%/RimModManager/` |
| macOS | `~/Library/Application Support/RimModManager/` |
| Linux | `~/.config/rimmodmanager/` |

---

## 🔧 Troubleshooting

<details>
<summary><b>SteamCMD not found</b></summary>

| Platform | Solution |
|----------|----------|
| Windows | Download from [Steam](https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip) or `choco install steamcmd` |
| macOS | `brew install steamcmd` |
| Arch Linux | `yay -S steamcmd` |
| Ubuntu | `sudo apt install steamcmd` |
</details>

<details>
<summary><b>No installations detected</b></summary>

On first launch, the **Auto-Setup Wizard** will automatically scan your system. You can also:
- Click "🔄 Detect" to re-scan
- Click "➕ Add Custom" and browse to your RimWorld folder
- Supported: Steam, GOG, Lutris, Bottles, Heroic, and standalone installs
</details>

<details>
<summary><b>Mods not showing in game</b></summary>

1. Make sure you clicked "Apply Load Order"
2. Check if symlinks were created in your game's Mods folder
3. On Windows, you may need to run as Administrator for symlinks
</details>

---

## 🤝 Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

- 🐛 [Report bugs](https://github.com/MrXploisLite/RimModManager/issues/new?template=bug_report.md)
- 💡 [Request features](https://github.com/MrXploisLite/RimModManager/issues/new?template=feature_request.md)
- 🔧 [Submit PRs](https://github.com/MrXploisLite/RimModManager/pulls)

---

## 📜 License

**GPL-3.0 License** - See [LICENSE](LICENSE) for details.

If you fork or distribute this code, you must:
- Keep the source code open
- Include the original license
- State your changes
- Use GPL-3.0 license

---

<div align="center">

**⭐ Star this repo if you find it useful!**

</div>
