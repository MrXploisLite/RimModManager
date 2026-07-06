"""
Regression tests for v0.2.5 - Game detection and fullscreen.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path


class TestLinuxStandaloneDetection(unittest.TestCase):
    """Test Linux standalone (GOG/manual) detection."""
    
    @unittest.skipUnless(sys.platform.startswith("linux"), "Linux standalone detection runs only on Linux")
    def test_detects_standalone_in_home(self):
        """Should detect RimWorld in ~/RimWorld/ with nested structure."""
        from game_detector import GameDetector, InstallationType
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Simulate GOG installer structure
            game_dir = Path(tmpdir) / "RimWorld" / "rimworld_linux" / "data" / "noarch" / "game"
            game_dir.mkdir(parents=True)
            
            # Create binary
            binary = game_dir / "RimWorldLinux"
            binary.touch()
            
            # Create Data folder with Core
            (game_dir / "Data" / "Core").mkdir(parents=True)
            
            # Create Mods folder
            (game_dir / "Mods").mkdir()
            
            detector = GameDetector()
            # Patch home to use our temp dir
            import unittest.mock
            with unittest.mock.patch.object(Path, 'home', return_value=Path(tmpdir)):
                detector = GameDetector()
                installations = detector.detect_all()
            
            # Should find the installation
            standalone_installs = [i for i in installations if i.install_type == InstallationType.STANDALONE]
            self.assertGreater(len(standalone_installs), 0)
    
    def test_detects_valid_rimworld_with_data_core(self):
        """Should detect valid RimWorld by Data/Core folder."""
        from game_detector import GameDetector
        
        with tempfile.TemporaryDirectory() as tmpdir:
            game_dir = Path(tmpdir) / "game"
            game_dir.mkdir()
            
            (game_dir / "Data" / "Core").mkdir(parents=True)
            (game_dir / "Mods").mkdir()
            
            detector = GameDetector()
            self.assertTrue(detector._is_valid_rimworld(game_dir))
    
    def test_detects_valid_rimworld_with_binary(self):
        """Should detect valid RimWorld by RimWorldLinux binary."""
        from game_detector import GameDetector
        
        with tempfile.TemporaryDirectory() as tmpdir:
            game_dir = Path(tmpdir) / "game"
            game_dir.mkdir()
            
            binary = game_dir / "RimWorldLinux"
            binary.touch()
            
            detector = GameDetector()
            self.assertTrue(detector._is_valid_rimworld(game_dir))
    
    def test_rejects_empty_directory(self):
        """Should reject empty directories."""
        from game_detector import GameDetector
        
        with tempfile.TemporaryDirectory() as tmpdir:
            empty_dir = Path(tmpdir) / "empty"
            empty_dir.mkdir()
            
            detector = GameDetector()
            self.assertFalse(detector._is_valid_rimworld(empty_dir))


class TestWindowMaximizedConfig(unittest.TestCase):
    """Test window maximized state in config."""
    
    def test_window_maximized_field_exists(self):
        """Config should have window_maximized field."""
        from config_handler import AppConfig
        
        config = AppConfig()
        self.assertTrue(hasattr(config, 'window_maximized'))
        self.assertIsInstance(config.window_maximized, bool)
        self.assertFalse(config.window_maximized)
    
    def test_window_maximized_validation(self):
        """window_maximized should be validated as boolean."""
        from config_handler import ConfigHandler
        
        handler = ConfigHandler()
        
        # Valid boolean
        valid, value = handler._validate_loaded_value('window_maximized', True)
        self.assertTrue(valid)
        self.assertTrue(value)
        
        # Invalid: string
        valid, value = handler._validate_loaded_value('window_maximized', "true")
        self.assertFalse(valid)
        
        # Invalid: int
        valid, value = handler._validate_loaded_value('window_maximized', 1)
        self.assertFalse(valid)


class TestFullscreenCodeExists(unittest.TestCase):
    """Test that fullscreen code exists in main_window.py."""
    
    def test_toggle_fullscreen_method_exists(self):
        """main_window.py should have _toggle_fullscreen method."""
        with open("ui/main_window.py", 'r') as f:
            content = f.read()
        
        self.assertIn("def _toggle_fullscreen", content)
        self.assertIn("WindowFullScreen", content)
        self.assertIn("setWindowState", content)
    
    def test_f11_shortcut_exists(self):
        """F11 shortcut should be set for fullscreen."""
        with open("ui/main_window.py", 'r') as f:
            content = f.read()
        
        self.assertIn('"F11"', content)
    
    def test_view_menu_exists(self):
        """View menu should exist in menu bar."""
        with open("ui/main_window.py", 'r') as f:
            content = f.read()
        
        self.assertIn('addMenu("View")', content)
    
    def test_reset_window_size_exists(self):
        """Reset window size method should exist."""
        with open("ui/main_window.py", 'r') as f:
            content = f.read()
        
        self.assertIn("def _reset_window_size", content)
    
    def test_close_event_saves_maximized(self):
        """closeEvent should save window_maximized state."""
        with open("ui/main_window.py", 'r') as f:
            content = f.read()
        
        self.assertIn("window_maximized", content)
        self.assertIn("isMaximized", content)
    
    def test_restore_maximized_on_startup(self):
        """Should restore maximized state on startup."""
        with open("ui/main_window.py", 'r') as f:
            content = f.read()
        
        self.assertIn("showMaximized", content)


if __name__ == '__main__':
    unittest.main()
