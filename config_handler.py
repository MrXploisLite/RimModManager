"""
Configuration Handler for RimModManager
Cross-platform configuration storage.
- Windows: %APPDATA%/RimModManager/
- macOS: ~/Library/Application Support/RimModManager/
- Linux: ~/.config/rimmodmanager/
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, field, asdict

# Module logger
log = logging.getLogger("rimmodmanager.config")


def get_platform() -> str:
    """Get current platform: 'windows', 'macos', or 'linux'."""
    if sys.platform.startswith('win') or sys.platform in ('cygwin', 'msys'):
        return 'windows'
    elif sys.platform == 'darwin':
        return 'macos'
    else:
        return 'linux'


PLATFORM = get_platform()


@dataclass
class AppConfig:
    """Application configuration data class."""
    # Last selected game installation path
    last_installation: str = ""
    
    # Custom mod source directories (user can add multiple)
    mod_source_paths: list[str] = field(default_factory=list)
    
    # Custom game installation paths (user-defined)
    custom_game_paths: list[str] = field(default_factory=list)
    
    # Last used modlist file path
    last_modlist_path: str = ""
    
    # Window geometry
    window_width: int = 1200
    window_height: int = 800
    window_x: int = -1
    window_y: int = -1
    window_maximized: bool = False
    
    # SteamCMD path (if not in PATH)
    steamcmd_path: str = ""
    
    # Workshop download directory
    workshop_download_path: str = ""
    
    # Remember splitter positions
    splitter_sizes: list[int] = field(default_factory=lambda: [300, 600, 300])
    
    # Dark mode preference (None = system, True = dark, False = light)
    dark_mode: Optional[bool] = None
    
    # Theme preference: "System", "Dark", "Light"
    theme: str = "System"
    
    # Active mods list (package IDs in load order) - per installation
    active_mods: dict[str, list[str]] = field(default_factory=dict)
    
    # Auto-update settings
    check_updates_on_startup: bool = False
    
    # Performance settings
    disable_webengine: bool = False  # Disable WebEngine for lower memory usage
    
    # First run flag - show setup wizard on first launch
    first_run: bool = True
    
    # Config path overrides per installation (for standalone/Wine games)
    # Key: installation path, Value: config folder path
    config_path_overrides: dict[str, str] = field(default_factory=dict)


class ConfigHandler:
    """
    Handles loading, saving, and accessing application configuration.
    Cross-platform config directory support.
    """
    
    CONFIG_DIR_NAME = "RimModManager" if PLATFORM == 'windows' else "rimmodmanager"
    CONFIG_FILE_NAME = "config.json"
    MODLISTS_DIR_NAME = "modlists"
    VALID_THEMES = {"System", "Dark", "Light"}
    
    def __init__(self):
        self._config_dir = self._get_config_dir()
        self._config_file = self._config_dir / self.CONFIG_FILE_NAME
        self._modlists_dir = self._config_dir / self.MODLISTS_DIR_NAME
        self._config: AppConfig = AppConfig()
        
        # Ensure directories exist
        self._ensure_directories()
        
        # Load existing config
        self.load()
    
    def _get_config_dir(self) -> Path:
        """Get platform-specific config directory."""
        if PLATFORM == 'windows':
            # Windows: %APPDATA%/RimModManager/
            appdata = os.environ.get('APPDATA')
            if appdata:
                return Path(appdata) / self.CONFIG_DIR_NAME
            return Path.home() / 'AppData' / 'Roaming' / self.CONFIG_DIR_NAME
        
        elif PLATFORM == 'macos':
            # macOS: ~/Library/Application Support/RimModManager/
            return Path.home() / 'Library' / 'Application Support' / self.CONFIG_DIR_NAME
        
        else:
            # Linux: XDG config directory
            xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
            if xdg_config_home:
                base = Path(xdg_config_home)
            else:
                base = Path.home() / ".config"
            return base / self.CONFIG_DIR_NAME
    
    def _ensure_directories(self) -> None:
        """Create config directories if they don't exist."""
        self._config_dir.mkdir(parents=True, exist_ok=True)
        self._modlists_dir.mkdir(parents=True, exist_ok=True)
    
    @property
    def config_dir(self) -> Path:
        """Return the configuration directory path."""
        return self._config_dir
    
    @property
    def modlists_dir(self) -> Path:
        """Return the modlists directory path."""
        return self._modlists_dir
    
    @property
    def config(self) -> AppConfig:
        """Return the current configuration."""
        return self._config

    def _validate_loaded_value(self, key: str, value: Any) -> tuple[bool, Any]:
        """Validate and sanitize value loaded from config file."""
        string_keys = {
            'last_installation',
            'last_modlist_path',
            'steamcmd_path',
            'workshop_download_path',
            'theme',
        }
        int_keys = {
            'window_width',
            'window_height',
            'window_x',
            'window_y',
        }
        bool_keys = {
            'check_updates_on_startup',
            'disable_webengine',
            'window_maximized',
            'first_run',
        }

        if key in string_keys:
            if not isinstance(value, str):
                return False, None
            if key == 'theme' and value not in self.VALID_THEMES:
                return False, None
            return True, value

        if key in int_keys:
            if isinstance(value, bool) or not isinstance(value, int):
                return False, None
            return True, value

        if key in bool_keys:
            return isinstance(value, bool), value

        if key in {'mod_source_paths', 'custom_game_paths'}:
            if not isinstance(value, list):
                return False, None
            cleaned = [v for v in value if isinstance(v, str) and v]
            return True, cleaned

        if key == 'splitter_sizes':
            if not isinstance(value, list):
                return False, None
            cleaned = [v for v in value if isinstance(v, int) and not isinstance(v, bool) and v >= 0]
            return (len(cleaned) >= 2), cleaned

        if key == 'active_mods':
            if not isinstance(value, dict):
                return False, None
            cleaned: dict[str, list[str]] = {}
            for install_path, mod_ids in value.items():
                if not isinstance(install_path, str) or not isinstance(mod_ids, list):
                    continue
                cleaned_ids = [m for m in mod_ids if isinstance(m, str) and m]
                cleaned[install_path] = cleaned_ids
            return True, cleaned

        if key == 'dark_mode':
            if value is None or isinstance(value, bool):
                return True, value
            return False, None

        if key == 'config_path_overrides':
            if not isinstance(value, dict):
                return False, None
            cleaned = {
                k: v for k, v in value.items()
                if isinstance(k, str) and isinstance(v, str) and k and v
            }
            return True, cleaned

        return True, value
    
    def load(self) -> bool:
        """
        Load configuration from file.
        Returns True if loaded successfully, False otherwise.
        """
        if not self._config_file.exists():
            return False
        
        try:
            with open(self._config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate data is a dict
            if not isinstance(data, dict):
                log.warning("Config file is not a valid JSON object")
                return False
            
            # Update config with loaded values, keeping defaults for missing keys
            for key, value in data.items():
                if hasattr(self._config, key):
                    valid, sanitized = self._validate_loaded_value(key, value)
                    if not valid:
                        log.warning(f"Ignoring invalid config value for '{key}'")
                        continue
                    setattr(self._config, key, sanitized)
            
            return True
        except (json.JSONDecodeError, IOError, PermissionError, TypeError) as e:
            log.warning(f"Failed to load config: {e}")
            return False
    
    def save(self) -> bool:
        """
        Save configuration to file using atomic write.
        Returns True if saved successfully, False otherwise.
        """
        import tempfile
        
        try:
            # Write to temp file first, then atomic rename
            fd, temp_path = tempfile.mkstemp(
                suffix='.json',
                prefix='config_',
                dir=self._config_dir
            )
            try:
                with os.fdopen(fd, 'w', encoding='utf-8') as f:
                    json.dump(asdict(self._config), f, indent=2)
                
                # Atomic rename (works on POSIX, best-effort on Windows)
                temp_file = Path(temp_path)
                temp_file.replace(self._config_file)
                return True
            except (IOError, OSError, TypeError, ValueError):
                # Clean up temp file on error
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
                raise
        except (IOError, PermissionError, OSError) as e:
            log.error(f"Failed to save config: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key."""
        return getattr(self._config, key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value and save."""
        if hasattr(self._config, key):
            setattr(self._config, key, value)
            self.save()
    
    def add_mod_source_path(self, path: str) -> bool:
        """Add a mod source directory if not already present."""
        if path and path not in self._config.mod_source_paths:
            self._config.mod_source_paths.append(path)
            self.save()
            return True
        return False
    
    def remove_mod_source_path(self, path: str) -> bool:
        """Remove a mod source directory."""
        if path in self._config.mod_source_paths:
            self._config.mod_source_paths.remove(path)
            self.save()
            return True
        return False
    
    def add_custom_game_path(self, path: str) -> bool:
        """Add a custom game installation path."""
        if path and path not in self._config.custom_game_paths:
            self._config.custom_game_paths.append(path)
            self.save()
            return True
        return False
    
    def remove_custom_game_path(self, path: str) -> bool:
        """Remove a custom game installation path."""
        if path in self._config.custom_game_paths:
            self._config.custom_game_paths.remove(path)
            self.save()
            return True
        return False
    
    def get_default_workshop_path(self) -> Path:
        """Get default path for workshop downloads."""
        if self._config.workshop_download_path:
            return Path(self._config.workshop_download_path)
        
        # Default to a directory in user's home
        default = Path.home() / "RimWorld_Workshop_Mods"
        return default
    
    def save_modlist(self, name: str, mod_ids: list[str], active_mods: list[str]) -> Path:
        """
        Save a modlist to the modlists directory.
        Returns the path to the saved file.
        """
        import tempfile
        
        modlist_data = {
            "name": name,
            "mod_ids": mod_ids,
            "active_mods": active_mods
        }
        
        # Sanitize filename - prevent path traversal
        safe_name = "".join(c for c in name if c.isalnum() or c in "._- ")
        safe_name = safe_name.replace("..", "_")  # Prevent path traversal
        if not safe_name:
            safe_name = "unnamed_modlist"
        filename = f"{safe_name}.json"
        filepath = self._modlists_dir / filename
        
        # Atomic write
        temp_path = ""
        try:
            fd, temp_path = tempfile.mkstemp(
                suffix='.json',
                prefix='modlist_',
                dir=self._modlists_dir
            )
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump(modlist_data, f, indent=2)
            
            Path(temp_path).replace(filepath)
        except (IOError, OSError, TypeError, ValueError):
            try:
                if temp_path:
                    os.unlink(temp_path)
            except OSError:
                pass
            raise
        
        return filepath
    
    def load_modlist(self, filepath: Path) -> Optional[dict]:
        """Load a modlist from file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            log.warning(f"Failed to load modlist: {e}")
            return None
    
    def list_modlists(self) -> list[Path]:
        """List all saved modlists."""
        return list(self._modlists_dir.glob("*.json"))
    
    def save_active_mods(self, installation_path: str, mod_ids: list[str]) -> None:
        """
        Save active mods list for a specific installation.
        
        Args:
            installation_path: Path to the RimWorld installation
            mod_ids: List of package IDs in load order
        """
        self._config.active_mods[installation_path] = mod_ids
        self.save()
    
    def get_active_mods(self, installation_path: str) -> list[str]:
        """
        Get saved active mods list for a specific installation.
        
        Args:
            installation_path: Path to the RimWorld installation
            
        Returns:
            List of package IDs in load order, or empty list if none saved
        """
        return self._config.active_mods.get(installation_path, [])

    
    def set_config_path_override(self, installation_path: str, config_path: str) -> None:
        """
        Set a custom config path override for an installation.
        Useful for standalone/Wine games where auto-detection fails.
        """
        if config_path:
            self._config.config_path_overrides[installation_path] = config_path
        elif installation_path in self._config.config_path_overrides:
            del self._config.config_path_overrides[installation_path]
        self.save()
    
    def get_config_path_override(self, installation_path: str) -> Optional[str]:
        """Get custom config path override for an installation."""
        return self._config.config_path_overrides.get(installation_path)
