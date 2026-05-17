"""
Regression tests for v0.2.4 - Network resilience and input validation.
"""

import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestWorkshopIDValidation(unittest.TestCase):
    """Test workshop ID extraction and validation."""
    
    def _extract_workshop_id(self, url: str):
        """Extract workshop ID using same logic as WorkshopBrowser."""
        patterns = [
            r'steamcommunity\.com/sharedfiles/filedetails/\?id=(\d+)',
            r'steamcommunity\.com/workshop/filedetails/\?id=(\d+)',
            r'\?id=(\d+)',
            r'^(\d{7,12})$',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                workshop_id = match.group(1)
                if workshop_id.isdigit() and 1000000 <= int(workshop_id) <= 999999999999:
                    return workshop_id
        
        return None
    
    def test_valid_workshop_id_from_url(self):
        """Should extract valid workshop ID from URL."""
        self.assertEqual(
            self._extract_workshop_id("https://steamcommunity.com/sharedfiles/filedetails/?id=2009463077"),
            "2009463077"
        )
        self.assertEqual(
            self._extract_workshop_id("https://steamcommunity.com/workshop/filedetails/?id=818773962"),
            "818773962"
        )
    
    def test_valid_workshop_id_direct(self):
        """Should accept direct workshop ID."""
        self.assertEqual(self._extract_workshop_id("2009463077"), "2009463077")
    
    def test_invalid_workshop_id_too_short(self):
        """Should reject IDs that are too short."""
        self.assertIsNone(self._extract_workshop_id("123456"))
    
    def test_invalid_workshop_id_too_long(self):
        """Should reject IDs that are too long."""
        self.assertIsNone(self._extract_workshop_id("1234567890123"))
    
    def test_invalid_workshop_id_non_numeric(self):
        """Should reject non-numeric input."""
        self.assertIsNone(self._extract_workshop_id("abc123456"))
        self.assertIsNone(self._extract_workshop_id("not-a-number"))
    
    def test_invalid_workshop_id_empty(self):
        """Should reject empty input."""
        self.assertIsNone(self._extract_workshop_id(""))
        self.assertIsNone(self._extract_workshop_id("   "))


class TestCompatibilityDBCacheCorruption(unittest.TestCase):
    """Test cache corruption handling in CompatibilityDatabase."""
    
    def test_corrupted_cache_removed(self):
        """Should detect and remove corrupted cache files."""
        from compatibility_db import CompatibilityDatabase
        
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            db = CompatibilityDatabase(cache_dir)
            
            # Write corrupted cache
            db.cache_file.write_text("not valid json {{{")
            db.meta_file.write_text("also corrupted")
            
            # Should fail to load and remove corrupted files
            result = db.load_from_cache()
            self.assertFalse(result)
            self.assertFalse(db.cache_file.exists())
    
    def test_invalid_cache_structure_removed(self):
        """Should remove cache with invalid structure (not a dict)."""
        from compatibility_db import CompatibilityDatabase
        
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            db = CompatibilityDatabase(cache_dir)
            
            # Write cache with wrong structure
            db.cache_file.write_text(json.dumps(["wrong", "structure"]))
            
            result = db.load_from_cache()
            self.assertFalse(result)
            self.assertFalse(db.cache_file.exists())
    
    def test_corrupted_metadata_uses_defaults(self):
        """Should load cache even if metadata is corrupted."""
        from compatibility_db import CompatibilityDatabase
        
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            db = CompatibilityDatabase(cache_dir)
            
            # Write valid cache but corrupted metadata
            valid_data = {"timestamp": 1234, "rules": {}}
            db.cache_file.write_text(json.dumps(valid_data))
            db.meta_file.write_text("corrupted metadata")
            
            result = db.load_from_cache()
            self.assertTrue(result)
            self.assertEqual(db._db.last_updated, 0)
            self.assertEqual(db._db.source_url, "")


class TestNetworkRetryLogic(unittest.TestCase):
    """Test that retry logic exists in network functions."""
    
    def test_download_manager_has_retry_logic(self):
        """Download manager should have retry logic for API calls."""
        with open("ui/download_manager.py", 'r') as f:
            content = f.read()
        
        self.assertIn("max_retries", content)
        self.assertIn("for attempt in range", content)
    
    def test_workshop_browser_has_retry_logic(self):
        """Workshop browser should have retry logic for API calls."""
        with open("ui/workshop_browser.py", 'r') as f:
            content = f.read()
        
        self.assertIn("max_retries", content)
        self.assertIn("for attempt in range", content)
    
    def test_compatibility_db_has_retry_logic(self):
        """Compatibility database should have retry logic."""
        with open("compatibility_db.py", 'r') as f:
            content = f.read()
        
        self.assertIn("max_retries", content)
        self.assertIn("for attempt in range", content)


class TestDownloadValidation(unittest.TestCase):
    """Test download manager validation."""
    
    def test_run_validates_steamcmd_path(self):
        """Download manager should validate SteamCMD path before starting."""
        with open("ui/download_manager.py", 'r') as f:
            content = f.read()
        
        self.assertIn("Validate SteamCMD path", content)
        self.assertIn("SteamCMD not found", content)
    
    def test_run_validates_download_directory(self):
        """Download manager should validate download directory write access."""
        with open("ui/download_manager.py", 'r') as f:
            content = f.read()
        
        self.assertIn("Cannot write to download directory", content)
        self.assertIn(".write_test", content)


class TestHTTPErrorHandling(unittest.TestCase):
    """Test proper HTTP error handling."""
    
    def test_download_manager_handles_http_errors(self):
        """Download manager should handle HTTP errors specifically."""
        with open("ui/download_manager.py", 'r') as f:
            content = f.read()
        
        self.assertIn("urllib.error.HTTPError", content)
        self.assertIn("urllib.error.URLError", content)
    
    def test_workshop_browser_handles_http_errors(self):
        """Workshop browser should handle HTTP errors specifically."""
        with open("ui/workshop_browser.py", 'r') as f:
            content = f.read()
        
        self.assertIn("urllib.error.HTTPError", content)
        self.assertIn("urllib.error.URLError", content)


if __name__ == '__main__':
    unittest.main()
