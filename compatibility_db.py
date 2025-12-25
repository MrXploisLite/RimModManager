"""
Compatibility Database for RimModManager
Downloads and parses RimSort Community Rules Database.
"""

import json
import logging
import time
import urllib.request
import urllib.error
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

log = logging.getLogger("rimmodmanager.compatibility_db")

# RimSort Community Rules Database URL
COMMUNITY_RULES_URL = "https://raw.githubusercontent.com/RimSort/Community-Rules-Database/main/communityRules.json"

# Cache settings
CACHE_EXPIRY_HOURS = 24


@dataclass
class ModRule:
    """Sorting rules for a single mod."""
    package_id: str
    load_before: list[str] = field(default_factory=list)
    load_after: list[str] = field(default_factory=list)
    load_bottom: bool = False
    load_top: bool = False
    incompatible_with: list[str] = field(default_factory=list)


@dataclass
class CommunityRulesDB:
    """Container for community rules database."""
    timestamp: int = 0
    rules: dict[str, ModRule] = field(default_factory=dict)
    last_updated: float = 0
    source_url: str = ""


class CompatibilityDatabase:
    """
    Manages the RimSort Community Rules Database.
    Downloads, caches, and provides access to mod sorting rules.
    """
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_file = cache_dir / "communityRules.json"
        self.meta_file = cache_dir / "communityRules_meta.json"
        self._db: Optional[CommunityRulesDB] = None
        
        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    @property
    def is_loaded(self) -> bool:
        """Check if database is loaded."""
        return self._db is not None and len(self._db.rules) > 0
    
    @property
    def rule_count(self) -> int:
        """Get number of rules in database."""
        return len(self._db.rules) if self._db else 0
    
    @property
    def last_updated(self) -> float:
        """Get timestamp of last update."""
        return self._db.last_updated if self._db else 0
    
    def is_cache_valid(self) -> bool:
        """Check if cached database is still valid."""
        if not self.cache_file.exists() or not self.meta_file.exists():
            return False
        
        try:
            with open(self.meta_file, 'r') as f:
                meta = json.load(f)
            
            last_updated = meta.get("last_updated", 0)
            expiry = CACHE_EXPIRY_HOURS * 3600
            
            return (time.time() - last_updated) < expiry
        except (json.JSONDecodeError, IOError):
            return False
    
    def load_from_cache(self) -> bool:
        """Load database from cache file."""
        if not self.cache_file.exists():
            return False
        
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self._db = self._parse_rules(data)
            
            # Load metadata
            if self.meta_file.exists():
                with open(self.meta_file, 'r') as f:
                    meta = json.load(f)
                self._db.last_updated = meta.get("last_updated", 0)
                self._db.source_url = meta.get("source_url", "")
            
            log.info(f"Loaded {self.rule_count} rules from cache")
            return True
            
        except (json.JSONDecodeError, IOError) as e:
            log.error(f"Failed to load cache: {e}")
            return False

    def download(self, timeout: int = 30) -> bool:
        """
        Download fresh database from GitHub.
        
        Args:
            timeout: Request timeout in seconds
            
        Returns:
            True if download successful
        """
        log.info(f"Downloading community rules from {COMMUNITY_RULES_URL}")
        
        try:
            req = urllib.request.Request(
                COMMUNITY_RULES_URL,
                headers={
                    'User-Agent': 'RimModManager/2.0',
                    'Accept': 'application/json',
                }
            )
            
            with urllib.request.urlopen(req, timeout=timeout) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            # Parse and store
            self._db = self._parse_rules(data)
            self._db.last_updated = time.time()
            self._db.source_url = COMMUNITY_RULES_URL
            
            # Save to cache
            self._save_cache(data)
            
            log.info(f"Downloaded {self.rule_count} rules")
            return True
            
        except urllib.error.URLError as e:
            log.error(f"Network error downloading rules: {e}")
            return False
        except json.JSONDecodeError as e:
            log.error(f"Invalid JSON in rules database: {e}")
            return False
        except Exception as e:
            log.error(f"Unexpected error downloading rules: {e}")
            return False
    
    def _save_cache(self, data: dict) -> None:
        """Save database to cache files."""
        try:
            # Save raw data
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f)
            
            # Save metadata
            meta = {
                "last_updated": time.time(),
                "source_url": COMMUNITY_RULES_URL,
                "rule_count": self.rule_count,
            }
            with open(self.meta_file, 'w') as f:
                json.dump(meta, f)
                
        except IOError as e:
            log.warning(f"Failed to save cache: {e}")
    
    def _parse_rules(self, data: dict) -> CommunityRulesDB:
        """Parse raw JSON data into CommunityRulesDB."""
        db = CommunityRulesDB()
        db.timestamp = data.get("timestamp", 0)
        
        rules_data = data.get("rules", {})
        
        for package_id, rule_data in rules_data.items():
            rule = ModRule(package_id=package_id.lower())
            
            # Parse loadBefore
            load_before = rule_data.get("loadBefore", {})
            for target_id in load_before.keys():
                rule.load_before.append(target_id.lower())
            
            # Parse loadAfter
            load_after = rule_data.get("loadAfter", {})
            for target_id in load_after.keys():
                rule.load_after.append(target_id.lower())
            
            # Parse loadBottom
            load_bottom = rule_data.get("loadBottom", {})
            if isinstance(load_bottom, dict) and load_bottom.get("value"):
                rule.load_bottom = True
            
            # Parse loadTop
            load_top = rule_data.get("loadTop", {})
            if isinstance(load_top, dict) and load_top.get("value"):
                rule.load_top = True
            
            # Parse incompatibleWith
            incompatible = rule_data.get("incompatibleWith", {})
            for target_id in incompatible.keys():
                rule.incompatible_with.append(target_id.lower())
            
            db.rules[package_id.lower()] = rule
        
        return db
    
    def get_rule(self, package_id: str) -> Optional[ModRule]:
        """Get sorting rule for a mod."""
        if not self._db:
            return None
        return self._db.rules.get(package_id.lower())
    
    def get_load_order_issues(self, mod_order: list[str]) -> list[dict]:
        """
        Check mod order against community rules.
        
        Args:
            mod_order: List of package IDs in current load order
            
        Returns:
            List of issues found
        """
        if not self._db:
            return []
        
        issues = []
        mod_positions = {pid.lower(): i for i, pid in enumerate(mod_order)}
        
        for i, package_id in enumerate(mod_order):
            pid_lower = package_id.lower()
            rule = self._db.rules.get(pid_lower)
            
            if not rule:
                continue
            
            # Check loadBefore violations
            for should_be_after in rule.load_before:
                if should_be_after in mod_positions:
                    if mod_positions[should_be_after] < i:
                        issues.append({
                            "type": "load_order",
                            "mod": package_id,
                            "target": should_be_after,
                            "message": f"'{package_id}' should load BEFORE '{should_be_after}'",
                            "severity": "warning",
                        })
            
            # Check loadAfter violations
            for should_be_before in rule.load_after:
                if should_be_before in mod_positions:
                    if mod_positions[should_be_before] > i:
                        issues.append({
                            "type": "load_order",
                            "mod": package_id,
                            "target": should_be_before,
                            "message": f"'{package_id}' should load AFTER '{should_be_before}'",
                            "severity": "warning",
                        })
            
            # Check incompatibilities
            for incompat in rule.incompatible_with:
                if incompat in mod_positions:
                    issues.append({
                        "type": "incompatible",
                        "mod": package_id,
                        "target": incompat,
                        "message": f"'{package_id}' is INCOMPATIBLE with '{incompat}'",
                        "severity": "error",
                    })
        
        return issues
    
    def suggest_sort_order(self, mods: list[str]) -> list[str]:
        """
        Suggest optimal load order based on community rules.
        Uses topological sort with rule priorities.
        
        Args:
            mods: List of package IDs to sort
            
        Returns:
            Sorted list of package IDs
        """
        if not self._db:
            return mods
        
        from collections import deque
        
        mods_lower = [m.lower() for m in mods]
        mod_set = set(mods_lower)
        
        # Build dependency graph
        # edges[a] = [b, c] means a should come before b and c
        edges: dict[str, list[str]] = {m: [] for m in mods_lower}
        in_degree: dict[str, int] = {m: 0 for m in mods_lower}
        
        for mod in mods_lower:
            rule = self._db.rules.get(mod)
            if not rule:
                continue
            
            # loadBefore: this mod should come before targets
            for target in rule.load_before:
                if target in mod_set:
                    edges[mod].append(target)
                    in_degree[target] += 1
            
            # loadAfter: targets should come before this mod
            for target in rule.load_after:
                if target in mod_set:
                    edges[target].append(mod)
                    in_degree[mod] += 1
        
        # Separate loadTop and loadBottom mods
        top_mods = []
        bottom_mods = []
        middle_mods = []
        
        for mod in mods_lower:
            rule = self._db.rules.get(mod)
            if rule and rule.load_top:
                top_mods.append(mod)
            elif rule and rule.load_bottom:
                bottom_mods.append(mod)
            else:
                middle_mods.append(mod)
        
        # Topological sort for middle mods
        queue = deque([m for m in middle_mods if in_degree.get(m, 0) == 0])
        sorted_middle = []
        
        while queue:
            mod = queue.popleft()
            if mod in middle_mods:
                sorted_middle.append(mod)
            
            for neighbor in edges.get(mod, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0 and neighbor in middle_mods:
                    queue.append(neighbor)
        
        # Add any remaining mods (cycle handling)
        remaining = [m for m in middle_mods if m not in sorted_middle]
        sorted_middle.extend(remaining)
        
        # Combine: top + sorted_middle + bottom
        result = top_mods + sorted_middle + bottom_mods
        
        # Map back to original case
        original_case = {m.lower(): m for m in mods}
        return [original_case.get(m, m) for m in result]
    
    def get_stats(self) -> dict:
        """Get database statistics."""
        if not self._db:
            return {"loaded": False}
        
        return {
            "loaded": True,
            "rule_count": self.rule_count,
            "timestamp": self._db.timestamp,
            "last_updated": self._db.last_updated,
            "source_url": self._db.source_url,
        }
