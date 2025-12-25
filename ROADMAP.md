# RimModManager Roadmap

## Version 2.0 - Big Update

### Overview
7 major features to enhance mod management experience.

---

## Features

### 1. Better Search/Filter ✅
**Status**: Complete  
**Priority**: High  
**Effort**: Low

**Description**: Enhanced search and filtering for mod lists.

**Features**:
- [x] Real-time search by name, author, package ID
- [x] Filter by source (Workshop/Local/DLC)
- [x] Filter by category
- [x] Search with debounce (150ms)
- [x] Multiple search terms (AND logic)

**Files**:
- `ui/mod_widgets.py` - ModSearchFilter widget

---

### 2. Mod Categories ✅
**Status**: Complete  
**Priority**: High  
**Effort**: Low

**Description**: Auto-categorize mods based on keywords and patterns.

**Categories**:
- 🔧 Framework
- ✨ Quality of Life
- ⚔️ Combat & Weapons
- 🐾 Animals & Creatures
- 👥 Factions & Races
- 🏠 Buildings & Furniture
- 🔨 Crafting & Production
- 💊 Medical & Health
- 🔬 Research & Technology
- 📜 Events & Storyteller
- 🖥️ UI & Interface
- 🎨 Textures & Graphics
- 👕 Apparel & Armor
- 🚗 Vehicles
- 📦 Miscellaneous

**Features**:
- [x] Keyword-based categorization
- [x] Known mod database
- [x] Package ID pattern matching
- [x] Category filter in search
- [x] Category badges in mod list
- [x] Category display in details panel

**Files**:
- `mod_categories.py` - Categorization logic

---

### 3. Import from RimPy/RimSort ✅
**Status**: Complete  
**Priority**: High  
**Effort**: Low

**Description**: Import modlists from other mod managers.

**Supported Formats**:
- [x] RimSort JSON modlist
- [x] RimPy XML modlist
- [x] Game's ModsConfig.xml
- [x] Plain text (package IDs)
- [x] Workshop IDs list
- [x] RimModManager JSON

**Features**:
- [x] Auto-detect format
- [x] Import dialog with summary
- [x] Replace or merge options
- [x] Workshop ID download queue integration
- [x] Missing mod detection

**Files**:
- `mod_importer.py` - Import logic for various formats

---

### 4. Auto-Update Mods ✅
**Status**: Complete  
**Priority**: Medium  
**Effort**: Medium

**Description**: Check and download mod updates automatically.

**Features**:
- [x] Check all Workshop mods for updates (ModUpdateCheckerWidget)
- [x] Show update available indicator
- [x] Batch download updates via SteamCMD
- [x] Update notification on startup (optional setting)
- [x] Settings checkbox for auto-check on startup

**Files**:
- `mod_parser.py` - ModUpdateChecker class
- `ui/tools_widgets.py` - ModUpdateCheckerWidget
- `config_handler.py` - check_updates_on_startup setting
- `ui/main_window.py` - SettingsDialog checkbox, _check_updates_on_startup()

---

### 5. Mod Presets/Collections ✅
**Status**: Complete  
**Priority**: Medium  
**Effort**: Medium

**Description**: Share modlists via compact codes.

**Features**:
- [x] Export modlist as shareable code (base64+zlib)
- [x] Import from code
- [x] Copy code to clipboard
- [x] Replace or merge options
- [x] Workshop ID extraction for missing mods

**Format**:
```
RMM:v1:<base64_compressed_json>
```

**Menu**:
- File → Export as Shareable Code... (Ctrl+Shift+C)
- File → Import from Code... (Ctrl+Shift+V)

**Files**:
- `mod_presets.py` - PresetEncoder class (encode/decode)
- `ui/main_window.py` - _export_preset_code(), _import_preset_code(), _apply_preset()

---

### 6. Mod Conflict Visualization ✅
**Status**: Complete  
**Priority**: Medium  
**Effort**: Medium

**Description**: Visual graph showing mod dependencies and conflicts.

**Features**:
- [x] Interactive dependency graph (QGraphicsView)
- [x] Nodes = mods (draggable), Edges = dependencies
- [x] Color coding:
  - Green: Satisfied dependency
  - Red: Conflict/Incompatible
  - Yellow: Missing dependency
  - Blue: Load order issue
- [x] Click node to select mod in list
- [x] Zoom and pan (mouse wheel + drag)
- [x] Hierarchical and circular layouts
- [x] Filter by connection type

**Menu**: Tools → 🔗 Dependency Graph... (Ctrl+G)

**Files**:
- `ui/graph_view.py` - ModGraphView, ModNode, ModEdge, ConflictGraphDialog

---

### 7. Compatibility Database ✅
**Status**: Complete  
**Priority**: Medium  
**Effort**: Medium

**Description**: Use community-maintained sorting rules.

**Data Source**: RimSort Community Rules Database
- URL: https://github.com/RimSort/Community-Rules-Database
- Format: `communityRules.json`

**Features**:
- [x] Download community rules from GitHub
- [x] Apply rules to auto-sort (topological sort)
- [x] Cache locally with 24h expiry
- [x] Manual refresh option
- [x] Check load order against rules
- [x] Show issues with severity levels

**Menu**: Tools → 📚 Community Rules →
- Download/Update Rules...
- Check Load Order...
- Sort by Community Rules

**Files**:
- `compatibility_db.py` - CompatibilityDatabase class
- `ui/main_window.py` - _download_community_rules(), _check_community_rules(), _sort_by_community_rules()

---

## Implementation Order

```
Sprint 1 (Quick Wins): ✅ COMPLETE
├── 1. Better Search/Filter ✅
├── 2. Mod Categories ✅
└── 3. Import RimPy/RimSort ✅

Sprint 2 (Core Features): ✅ COMPLETE
├── 4. Auto-Update Mods ✅
└── 5. Mod Presets/Collections ✅

Sprint 3 (Advanced): ✅ COMPLETE
├── 6. Conflict Graph View ✅
└── 7. Compatibility Database ✅
```

🎉 **Version 2.0 Complete!**

---

## Technical Notes

### Dependencies
- No new dependencies required
- Uses existing PyQt6 components
- QGraphicsView for graph (built-in)

### File Structure
```
rimmodmanager/
├── mod_categories.py      # NEW: Auto-categorization ✅
├── mod_importer.py        # NEW: RimPy/RimSort import ✅
├── mod_presets.py         # NEW: Shareable collections ✅
├── compatibility_db.py    # NEW: Community rules DB ✅
├── ui/
│   └── graph_view.py      # NEW: Dependency graph ✅
```

### Data Formats

**RimSort Modlist JSON**:
```json
{
  "name": "My Modlist",
  "mods": ["packageid1", "packageid2", ...]
}
```

**Shareable Preset Code**:
```
RMM:v1:eJxLy0...base64...
```

**Community Rules JSON**:
```json
{
  "rules": {
    "package.id": {
      "loadBefore": ["other.mod"],
      "loadAfter": ["another.mod"]
    }
  }
}
```

---

## Changelog

### [Unreleased]
- Started roadmap planning
- Research completed for all features

---

*Last Updated: 2025-12-25*
