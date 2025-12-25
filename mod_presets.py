"""
Mod Presets for RimModManager
Shareable modlist codes using base64+zlib compression.
"""

import json
import zlib
import base64
import logging
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

log = logging.getLogger("rimmodmanager.mod_presets")

# Preset code format: RMM:v1:<base64_compressed_data>
PRESET_PREFIX = "RMM"
PRESET_VERSION = 1


@dataclass
class PresetData:
    """Data structure for a mod preset."""
    name: str
    package_ids: list[str]
    workshop_ids: list[str]
    created_at: str
    description: str = ""
    author: str = ""
    game_version: str = ""


class PresetEncoder:
    """Encode and decode mod presets as shareable codes."""
    
    @staticmethod
    def encode(
        package_ids: list[str],
        name: str = "Modlist",
        workshop_ids: list[str] = None,
        description: str = "",
        author: str = "",
        game_version: str = ""
    ) -> str:
        """
        Encode a modlist as a shareable code.
        
        Format: RMM:v1:<base64_zlib_compressed_json>
        """
        data = {
            "n": name,  # Short keys for smaller output
            "p": package_ids,
            "w": workshop_ids or [],
            "t": datetime.now().isoformat()[:19],
            "d": description,
            "a": author,
            "v": game_version,
        }
        
        # Remove empty fields to save space
        data = {k: v for k, v in data.items() if v}
        
        # Ensure package_ids is always present
        if "p" not in data:
            data["p"] = []
        
        try:
            # Convert to JSON
            json_str = json.dumps(data, separators=(',', ':'))
            
            # Compress with zlib
            compressed = zlib.compress(json_str.encode('utf-8'), level=9)
            
            # Encode as base64 (URL-safe)
            b64 = base64.urlsafe_b64encode(compressed).decode('ascii')
            
            # Build final code
            code = f"{PRESET_PREFIX}:v{PRESET_VERSION}:{b64}"
            
            log.info(f"Encoded preset with {len(package_ids)} mods, code length: {len(code)}")
            return code
            
        except Exception as e:
            log.error(f"Failed to encode preset: {e}")
            raise ValueError(f"Failed to encode preset: {e}")
    
    @staticmethod
    def decode(code: str) -> Optional[PresetData]:
        """
        Decode a shareable code back to preset data.
        
        Returns PresetData or None if invalid.
        """
        code = code.strip()
        
        # Validate format
        if not code.startswith(f"{PRESET_PREFIX}:"):
            log.warning(f"Invalid preset code prefix")
            return None
        
        parts = code.split(':', 2)
        if len(parts) != 3:
            log.warning(f"Invalid preset code format")
            return None
        
        prefix, version, b64_data = parts
        
        # Check version
        if not version.startswith('v'):
            log.warning(f"Invalid version format: {version}")
            return None
        
        try:
            ver_num = int(version[1:])
            if ver_num > PRESET_VERSION:
                log.warning(f"Preset version {ver_num} is newer than supported {PRESET_VERSION}")
                # Try to decode anyway
        except ValueError:
            log.warning(f"Invalid version number: {version}")
            return None
        
        try:
            # Decode base64
            compressed = base64.urlsafe_b64decode(b64_data)
            
            # Decompress
            json_str = zlib.decompress(compressed).decode('utf-8')
            
            # Parse JSON
            data = json.loads(json_str)
            
            # Build PresetData
            preset = PresetData(
                name=data.get("n", "Imported Preset"),
                package_ids=data.get("p", []),
                workshop_ids=data.get("w", []),
                created_at=data.get("t", ""),
                description=data.get("d", ""),
                author=data.get("a", ""),
                game_version=data.get("v", ""),
            )
            
            log.info(f"Decoded preset '{preset.name}' with {len(preset.package_ids)} mods")
            return preset
            
        except (base64.binascii.Error, zlib.error) as e:
            log.error(f"Failed to decode preset data: {e}")
            return None
        except json.JSONDecodeError as e:
            log.error(f"Failed to parse preset JSON: {e}")
            return None
        except Exception as e:
            log.error(f"Unexpected error decoding preset: {e}")
            return None
    
    @staticmethod
    def validate_code(code: str) -> tuple[bool, str]:
        """
        Validate a preset code without fully decoding.
        
        Returns (is_valid, message).
        """
        code = code.strip()
        
        if not code:
            return False, "Empty code"
        
        if not code.startswith(f"{PRESET_PREFIX}:"):
            return False, f"Code must start with '{PRESET_PREFIX}:'"
        
        parts = code.split(':', 2)
        if len(parts) != 3:
            return False, "Invalid code format"
        
        _, version, b64_data = parts
        
        if not version.startswith('v'):
            return False, "Invalid version format"
        
        if len(b64_data) < 10:
            return False, "Code data too short"
        
        # Try to decode
        preset = PresetEncoder.decode(code)
        if preset is None:
            return False, "Failed to decode preset data"
        
        if not preset.package_ids and not preset.workshop_ids:
            return False, "Preset contains no mods"
        
        return True, f"Valid preset: {len(preset.package_ids)} mods"
    
    @staticmethod
    def get_code_stats(code: str) -> dict:
        """Get statistics about a preset code."""
        preset = PresetEncoder.decode(code)
        if not preset:
            return {"valid": False}
        
        return {
            "valid": True,
            "name": preset.name,
            "mod_count": len(preset.package_ids),
            "workshop_count": len(preset.workshop_ids),
            "created_at": preset.created_at,
            "author": preset.author,
            "code_length": len(code),
        }


def create_preset_code(
    package_ids: list[str],
    name: str = "My Modlist",
    workshop_ids: list[str] = None,
    description: str = "",
) -> str:
    """Convenience function to create a preset code."""
    return PresetEncoder.encode(
        package_ids=package_ids,
        name=name,
        workshop_ids=workshop_ids,
        description=description,
    )


def load_preset_code(code: str) -> Optional[PresetData]:
    """Convenience function to load a preset code."""
    return PresetEncoder.decode(code)
