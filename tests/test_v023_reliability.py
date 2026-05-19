"""
Regression tests for v0.2.3 - Reliability improvements.
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestSteamCMDValidation(unittest.TestCase):
    """Test SteamCMD path validation in WorkshopDownloader."""
    
    def test_download_fails_without_steamcmd(self):
        """Download should fail gracefully when SteamCMD is not available."""
        from workshop_downloader import WorkshopDownloader, DownloadStatus
        
        downloader = WorkshopDownloader(
            download_path=Path(tempfile.mkdtemp()),
            steamcmd_path="/nonexistent/steamcmd/shim"
        )
        
        task = downloader.add_to_queue("123456789", "Test Mod")
        result = downloader._download_mod(task)
        
        self.assertFalse(result)
        self.assertEqual(task.status, DownloadStatus.FAILED)
        self.assertIn("not found", task.error_message)
    
    def test_download_fails_with_invalid_steamcmd_path(self):
        """Download should fail gracefully when SteamCMD path doesn't exist."""
        from workshop_downloader import WorkshopDownloader, DownloadStatus
        
        downloader = WorkshopDownloader(
            download_path=Path(tempfile.mkdtemp()),
            steamcmd_path="/nonexistent/path/to/steamcmd"
        )
        
        task = downloader.add_to_queue("123456789", "Test Mod")
        result = downloader._download_mod(task)
        
        self.assertFalse(result)
        self.assertEqual(task.status, DownloadStatus.FAILED)
        self.assertIn("not found", task.error_message)


class TestAtomicWrites(unittest.TestCase):
    """Test atomic write operations."""
    
    def test_config_atomic_write(self):
        """Config save should use atomic write (temp file + rename)."""
        from config_handler import ConfigHandler, AppConfig
        from dataclasses import asdict
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            config_file = config_dir / "config.json"
            
            handler = ConfigHandler()
            handler._config_dir = config_dir
            handler._config_file = config_file
            handler._modlists_dir = config_dir / "modlists"
            handler._modlists_dir.mkdir()
            
            handler._config.theme = "Dark"
            result = handler.save()
            
            self.assertTrue(result)
            self.assertTrue(config_file.exists())
            
            # Verify content
            with open(config_file, 'r') as f:
                data = json.load(f)
            self.assertEqual(data["theme"], "Dark")
    
    def test_modsconfig_atomic_write(self):
        """ModsConfig write should use atomic write."""
        from mod_parser import ModsConfigParser
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "Config"
            
            parser = ModsConfigParser()
            active_mods = ["test.mod", "another.mod"]
            
            result = parser.write_mods_config(config_dir, active_mods)
            
            self.assertTrue(result)
            mods_config = config_dir / "ModsConfig.xml"
            self.assertTrue(mods_config.exists())
            
            # Verify it's valid XML
            content = mods_config.read_text()
            self.assertIn("<ModsConfigData>", content)
            self.assertIn("test.mod", content.lower())


class TestBareExceptFixes(unittest.TestCase):
    """Test that bare except clauses have been replaced."""
    
    def test_build_script_no_bare_except(self):
        """build.py should not have bare except clauses."""
        with open("build.py", 'r') as f:
            content = f.read()
        
        # Check for bare except (except: without specific exception)
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith('except:') or stripped == 'except:':
                self.fail(f"Bare except found at line {i}: {stripped}")
    
    def test_workshop_downloader_no_bare_except(self):
        """workshop_downloader.py should not have bare except clauses."""
        with open("workshop_downloader.py", 'r') as f:
            content = f.read()
        
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith('except:') or stripped == 'except:':
                self.fail(f"Bare except found at line {i}: {stripped}")


class TestRetryLogic(unittest.TestCase):
    """Test retry logic in WorkshopDownloader."""
    
    def test_max_retries_constant_exists(self):
        """WorkshopDownloader should have MAX_RETRIES constant."""
        from workshop_downloader import WorkshopDownloader
        
        self.assertTrue(hasattr(WorkshopDownloader, 'MAX_RETRIES'))
        self.assertIsInstance(WorkshopDownloader.MAX_RETRIES, int)
        self.assertGreater(WorkshopDownloader.MAX_RETRIES, 0)


class TestSingleInstanceLock(unittest.TestCase):
    """Test single-instance lock in main.py."""
    
    def test_lock_file_created(self):
        """main.py should create a lock file on startup."""
        # This test just verifies the code structure exists
        with open("main.py", 'r') as f:
            content = f.read()
        
        self.assertIn("fcntl.flock", content)
        self.assertIn(".instance.lock", content)
        self.assertIn("atexit", content)


if __name__ == '__main__':
    unittest.main()
