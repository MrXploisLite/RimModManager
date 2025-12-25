# RimModManager Roadmap

## Version 2.0 - Big Update

### Overview
7 major features to enhance mod management experience.

---

## Features

### 1. Better Search/Filter ⏳
**Status**: In Progress  
**Priority**: High  
**Effort**: Low

**Description**: Enhanced search and filtering for mod lists.

**Features**:
- [x] Real-time search by name, author, package ID
- [ ] Filter by source (Workshop/Local/DLC)
- [ ] Filter by status (Active/Inactive)
- [ ] Filter by category
- [ ] Search history/suggestions

**Files**:
- `ui/mod_widgets.py` - Add search widget to mod lists

---

### 2. Mod Categories ⏳
**Status**: Pending  
**Priority**: High  
**Effort**: Low

**Description**: Auto-categorize mods based on tags and keywords.

**Categories**:
- QoL (Quality of Life)
- Combat & Weapons
- Animals & Creatures
- Factions & Races
- Buildings & Furniture
- Crafting & Production
- Medical & Health
- Research & Technology
- Events & Storyteller
- UI & Interface
- Misc

**Features**:
- [ ] Parse `<modTags>` from About.xml
- [ ] Keyword-based categorization
- [ ] Category filter in search
- [ ] Category badges in mod list

**Files**:
- `mod_categories.py` - Categorization logic

---

### 3. Import from RimPy/RimSort ⏳
**Status**: Pending  
**Priority**: High  
**Effort**: Low

**Description**: Import modlists from other mod managers.

**Supported Formats**:
- [ ] RimSort JSON modlist
- [ ] RimPy modlist export
- [ ] Game's ModsConfig.xml (already supported)
- [ ] Plain text (one mod ID per line)

**Features**:
- [ ] Import dialog with format detection
- [ ] Preview before import
- [ ] Merge or replace options

**Files**:
- `mod_importer.py` - Import logic for various formats

---

### 4. Auto-Update Mods ⏳
**Status**: Pending  
**Priority**: Medium  
**Effort**: Medium

**Description**: Check and download mod updates automatically.

**Features**:
- [ ] Check all Workshop mods for updates
- [ ] Show update available indicator
- [ ] Batch download updates via SteamCMD
- [ ] Update notification on startup (optional)
- [ ] Update history log

**Files**:
- `mod_parser.py` - Extend ModUpdateChecker
- `ui/tools_widgets.py` - Update dialog UI

---

### 5. Mod Presets/Collections ⏳
**Status**: Pending  
**Priority**: Medium  
**Effort**: Medium

**Description**: Share modlists via compact codes.

**Features**:
- [ ] Export modlist as shareable code (base64+zlib)
- [ ] Import from code
- [ ] Copy code to clipboard
- [ ] QR code generation (optional)
- [ ] Preset library (save multiple presets)

**Format**:
```
RMM:v1:<base64_compressed_json>
```

**Files**:
- `mod_presets.py` - Encode/decode logic

---

### 6. Mod Conflict Visualization ⏳
**Status**: Pending  
**Priority**: Medium  
**Effort**: Medium

**Description**: Visual graph showing mod dependencies and conflicts.

**Features**:
- [ ] Interactive dependency graph
- [ ] Nodes = mods, Edges = dependencies
- [ ] Color coding:
  - Green: Satisfied dependency
  - Red: Conflict/Incompatible
  - Yellow: Missing dependency
  - Blue: Load order issue
- [ ] Click node to select mod
- [ ] Zoom and pan
- [ ] Export graph as image

**Files**:
- `ui/graph_view.py` - QGraphicsView-based graph widget

---

### 7. Compatibility Database ⏳
**Status**: Pending  
**Priority**: Medium  
**Effort**: Medium

**Description**: Use community-maintained sorting rules.

**Data Source**: RimSort Community Rules Database
- URL: https://github.com/RimSort/Community-Rules-Database
- Format: `communityRules.json`

**Features**:
- [ ] Download community rules from GitHub
- [ ] Apply rules to auto-sort
- [ ] Cache locally with expiry
- [ ] Manual refresh option
- [ ] Show rule source in conflict info

**Files**:
- `compatibility_db.py` - Database download and parsing

---

## Implementation Order

```
Sprint 1 (Quick Wins):
├── 1. Better Search/Filter
├── 2. Mod Categories
└── 3. Import RimPy/RimSort

Sprint 2 (Core Features):
├── 4. Auto-Update Mods
└── 5. Mod Presets/Collections

Sprint 3 (Advanced):
├── 6. Conflict Graph View
└── 7. Compatibility Database
```

---

## Technical Notes

### Dependencies
- No new dependencies required
- Uses existing PyQt6 components
- QGraphicsView for graph (built-in)

### File Structure
```
rimmodmanager/
├── mod_categories.py      # NEW: Auto-categorization
├── mod_importer.py        # NEW: RimPy/RimSort import
├── mod_presets.py         # NEW: Shareable collections
├── compatibility_db.py    # NEW: Community rules DB
├── ui/
│   └── graph_view.py      # NEW: Dependency graph
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
