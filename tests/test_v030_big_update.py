"""
Regression tests for v0.3.0 - Big Update.
"""

import unittest
from pathlib import Path


class TestSetupWizardConfig(unittest.TestCase):
    """Test setup wizard configuration."""
    
    def test_first_run_field_exists(self):
        """Config should have first_run field."""
        from config_handler import AppConfig
        
        config = AppConfig()
        self.assertTrue(hasattr(config, 'first_run'))
        self.assertIsInstance(config.first_run, bool)
        self.assertTrue(config.first_run)  # Default is True
    
    def test_first_run_validation(self):
        """first_run should be validated as boolean."""
        from config_handler import ConfigHandler
        
        handler = ConfigHandler()
        
        valid, value = handler._validate_loaded_value('first_run', True)
        self.assertTrue(valid)
        self.assertTrue(value)
        
        valid, value = handler._validate_loaded_value('first_run', False)
        self.assertTrue(valid)
        self.assertFalse(value)
        
        # Invalid: string
        valid, value = handler._validate_loaded_value('first_run', "true")
        self.assertFalse(valid)


class TestExpandedGameDetection(unittest.TestCase):
    """Test expanded game detection methods."""
    
    def test_lutris_detection_method_exists(self):
        """GameDetector should have _detect_lutris method."""
        from game_detector import GameDetector
        
        self.assertTrue(hasattr(GameDetector, '_detect_lutris'))
    
    def test_bottles_detection_method_exists(self):
        """GameDetector should have _detect_bottles method."""
        from game_detector import GameDetector
        
        self.assertTrue(hasattr(GameDetector, '_detect_bottles'))
    
    def test_heroic_detection_method_exists(self):
        """GameDetector should have _detect_heroic method."""
        from game_detector import GameDetector
        
        self.assertTrue(hasattr(GameDetector, '_detect_heroic'))
    
    def test_search_prefix_method_exists(self):
        """GameDetector should have _search_prefix_for_rimworld method."""
        from game_detector import GameDetector
        
        self.assertTrue(hasattr(GameDetector, '_search_prefix_for_rimworld'))
    
    def test_parse_lutris_config_method_exists(self):
        """GameDetector should have _parse_lutris_config method."""
        from game_detector import GameDetector
        
        self.assertTrue(hasattr(GameDetector, '_parse_lutris_config'))
    
    def test_parse_heroic_config_method_exists(self):
        """GameDetector should have _parse_heroic_config method."""
        from game_detector import GameDetector
        
        self.assertTrue(hasattr(GameDetector, '_parse_heroic_config'))
    
    def test_detect_linux_standalone_calls_new_methods(self):
        """Linux detection should call Lutris, Bottles, Heroic methods."""
        with open("game_detector.py", 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn("self._detect_lutris()", content)
        self.assertIn("self._detect_bottles()", content)
        self.assertIn("self._detect_heroic()", content)


class TestSetupWizardModule(unittest.TestCase):
    """Test setup wizard module exists and has required components."""
    
    def test_setup_wizard_file_exists(self):
        """setup_wizard.py should exist."""
        self.assertTrue(Path("ui/setup_wizard.py").exists())
    
    def test_setup_wizard_class_exists(self):
        """SetupWizard class should be importable when PyQt6 is installed."""
        try:
            from ui.setup_wizard import SetupWizard
        except ImportError as exc:
            self.skipTest(f"PyQt6 is not installed: {exc}")
        
        self.assertTrue(hasattr(SetupWizard, 'setup_complete'))
    
    def test_setup_worker_class_exists(self):
        """SetupWorker class should be importable when PyQt6 is installed."""
        try:
            from ui.setup_wizard import SetupWorker
        except ImportError as exc:
            self.skipTest(f"PyQt6 is not installed: {exc}")
        
        self.assertTrue(hasattr(SetupWorker, 'run'))
    
    def test_setup_wizard_imported_in_main_window(self):
        """main_window.py should import SetupWizard."""
        with open("ui/main_window.py", 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn("from ui.setup_wizard import SetupWizard", content)
    
    def test_show_setup_wizard_method_exists(self):
        """MainWindow should have _show_setup_wizard method."""
        with open("ui/main_window.py", 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn("def _show_setup_wizard", content)
        self.assertIn("def _on_setup_complete", content)
    
    def test_first_run_check_in_init(self):
        """MainWindow __init__ should check first_run."""
        with open("ui/main_window.py", 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn("self.config.config.first_run", content)
        self.assertIn("_show_setup_wizard", content)


class TestNoFeatureLoss(unittest.TestCase):
    """Verify all existing features still exist (no feature loss)."""
    
    def test_all_existing_methods_still_exist(self):
        """Key methods should still exist in main_window.py."""
        with open("ui/main_window.py", 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Core features
        required_methods = [
            "_detect_installations",
            "_scan_mods",
            "_apply_mods",
            "_save_modlist",
            "_load_modlist",
            "_import_modlist",
            "_auto_sort_mods",
            "_launch_game",
            "_show_workshop_dialog",
            "_show_settings",
            "_show_dependency_graph",
            "_toggle_fullscreen",
            "closeEvent",
        ]
        
        for method in required_methods:
            self.assertIn(f"def {method}", content, f"Missing method: {method}")
    
    def test_all_ui_components_still_exist(self):
        """Key UI components should still exist."""
        with open("ui/main_window.py", 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_components = [
            "install_combo",
            "btn_play",
            "btn_workshop",
            "main_tabs",
            "available_list",
            "active_list",
            "details_panel",
            "status_bar",
            "menuBar",
        ]
        
        for component in required_components:
            self.assertIn(component, content, f"Missing component: {component}")
    
    def test_all_modules_still_imported(self):
        """All existing modules should still be imported."""
        with open("ui/main_window.py", 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_imports = [
            "ConfigHandler",
            "GameDetector",
            "ModParser",
            "WorkshopDownloader",
            "ModInstaller",
            "DraggableModList",
            "ModDetailsPanel",
            "WorkshopBrowser",
            "DownloadLogWidget",
        ]
        
        for imp in required_imports:
            self.assertIn(imp, content, f"Missing import: {imp}")

    def test_workshop_browser_download_completion_api_exists(self):
        """WorkshopBrowser should expose the API MainWindow calls after downloads complete."""
        with open("ui/workshop_browser.py", 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn("self._queue_lock", content)
        self.assertIn("def refresh_downloaded_ids", content)
        self.assertIn("def clear_completed", content)

class TestExpandedDetectionPaths(unittest.TestCase):
    """Test that new detection paths are covered."""
    
    def test_lutris_paths_in_code(self):
        """Lutris paths should be in game detector."""
        with open("game_detector.py", 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn(".local/share/lutris", content)
        self.assertIn(".config/lutris", content)
    
    def test_bottles_paths_in_code(self):
        """Bottles paths should be in game detector."""
        with open("game_detector.py", 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn(".var/app/com.usebottles.bottles", content)
        self.assertIn(".local/share/bottles", content)
    
    def test_heroic_paths_in_code(self):
        """Heroic paths should be in game detector."""
        with open("game_detector.py", 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn("Games/Heroic", content)
        self.assertIn(".config/heroic", content)


if __name__ == '__main__':
    unittest.main()
