#!/usr/bin/env python3
"""
Unit tests for mod_parser.py
Tests XML parsing, load order sorting, and ModsConfig.xml generation.
"""

import unittest
import tempfile
import shutil
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from mod_parser import ModParser, ModInfo, ModSource, ModsConfigParser


class TestModParser(unittest.TestCase):
    """Tests for ModParser class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parser = ModParser()
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_mock_mod(self, name, package_id, load_after=None, load_before=None):
        """Create a mock mod directory with About.xml."""
        mod_dir = self.temp_dir / name
        about_dir = mod_dir / "About"
        about_dir.mkdir(parents=True)
        
        load_after_xml = ""
        if load_after:
            items = "\n".join(f"        <li>{dep}</li>" for dep in load_after)
            load_after_xml = f"    <loadAfter>\n{items}\n    </loadAfter>"
        
        load_before_xml = ""
        if load_before:
            items = "\n".join(f"        <li>{dep}</li>" for dep in load_before)
            load_before_xml = f"    <loadBefore>\n{items}\n    </loadBefore>"
        
        about_xml = f'''<?xml version="1.0" encoding="utf-8"?>
<ModMetaData>
    <name>{name}</name>
    <packageId>{package_id}</packageId>
    <author>Test Author</author>
    <supportedVersions>
        <li>1.5</li>
    </supportedVersions>
{load_after_xml}
{load_before_xml}
</ModMetaData>'''
        
        (about_dir / "About.xml").write_text(about_xml, encoding='utf-8')
        return mod_dir
    
    def test_parse_valid_about_xml(self):
        """Test parsing a valid About.xml file."""
        self._create_mock_mod("TestMod", "test.mod.id")
        mods = self.parser.scan_directory(self.temp_dir, ModSource.LOCAL)
        
        self.assertEqual(len(mods), 1)
        self.assertEqual(mods[0].name, "TestMod")
        self.assertEqual(mods[0].package_id, "test.mod.id")
        self.assertEqual(mods[0].author, "Test Author")
        self.assertIn("1.5", mods[0].supported_versions)
    
    def test_parse_mod_with_dependencies(self):
        """Test parsing mod with loadAfter/loadBefore."""
        self._create_mock_mod(
            "DependentMod", 
            "dependent.mod",
            load_after=["brrainz.harmony", "ludeon.rimworld"],
            load_before=["some.other.mod"]
        )
        mods = self.parser.scan_directory(self.temp_dir, ModSource.LOCAL)
        
        self.assertEqual(len(mods), 1)
        self.assertIn("brrainz.harmony", mods[0].load_after)
        self.assertIn("ludeon.rimworld", mods[0].load_after)
        self.assertIn("some.other.mod", mods[0].load_before)
    
    def test_scan_empty_directory(self):
        """Test scanning an empty directory."""
        mods = self.parser.scan_directory(self.temp_dir, ModSource.LOCAL)
        self.assertEqual(len(mods), 0)
    
    def test_scan_nonexistent_directory(self):
        """Test scanning a non-existent directory."""
        fake_path = self.temp_dir / "nonexistent"
        mods = self.parser.scan_directory(fake_path, ModSource.LOCAL)
        self.assertEqual(len(mods), 0)


class TestLoadOrderSorting(unittest.TestCase):
    """Tests for load order sorting functionality."""
    
    def setUp(self):
        self.parser = ModParser()
    
    def _create_mod_info(self, name, package_id, load_after=None, load_before=None):
        """Create a ModInfo object for testing."""
        return ModInfo(
            name=name,
            package_id=package_id,
            path=Path("/fake/path"),
            source=ModSource.LOCAL,
            load_after=load_after or [],
            load_before=load_before or []
        )
    
    def test_harmony_always_first(self):
        """Test that Harmony is always sorted first."""
        mods = [
            self._create_mod_info("Some Mod", "some.mod"),
            self._create_mod_info("Harmony", "brrainz.harmony"),
            self._create_mod_info("Another Mod", "another.mod"),
        ]
        sorted_mods = self.parser.sort_by_load_order(mods)
        self.assertEqual(sorted_mods[0].package_id, "brrainz.harmony")
    
    def test_core_after_harmony(self):
        """Test that Core comes after Harmony."""
        mods = [
            self._create_mod_info("Core", "ludeon.rimworld"),
            self._create_mod_info("Harmony", "brrainz.harmony"),
            self._create_mod_info("Some Mod", "some.mod"),
        ]
        sorted_mods = self.parser.sort_by_load_order(mods)
        
        harmony_idx = next(i for i, m in enumerate(sorted_mods) if "harmony" in m.package_id.lower())
        core_idx = next(i for i, m in enumerate(sorted_mods) if m.package_id == "ludeon.rimworld")
        self.assertLess(harmony_idx, core_idx)
    
    def test_dlc_order(self):
        """Test that DLCs are sorted in correct order after Core."""
        mods = [
            self._create_mod_info("Anomaly", "ludeon.rimworld.anomaly"),
            self._create_mod_info("Core", "ludeon.rimworld"),
            self._create_mod_info("Royalty", "ludeon.rimworld.royalty"),
            self._create_mod_info("Ideology", "ludeon.rimworld.ideology"),
            self._create_mod_info("Biotech", "ludeon.rimworld.biotech"),
        ]
        sorted_mods = self.parser.sort_by_load_order(mods)
        indices = {m.package_id: i for i, m in enumerate(sorted_mods)}
        
        self.assertLess(indices["ludeon.rimworld"], indices["ludeon.rimworld.royalty"])
        self.assertLess(indices["ludeon.rimworld.royalty"], indices["ludeon.rimworld.ideology"])
        self.assertLess(indices["ludeon.rimworld.ideology"], indices["ludeon.rimworld.biotech"])
        self.assertLess(indices["ludeon.rimworld.biotech"], indices["ludeon.rimworld.anomaly"])
    
    def test_load_after_respected(self):
        """Test that loadAfter dependencies are respected."""
        mods = [
            self._create_mod_info("Dependent", "dependent.mod", load_after=["base.mod"]),
            self._create_mod_info("Base", "base.mod"),
        ]
        sorted_mods = self.parser.sort_by_load_order(mods)
        
        base_idx = next(i for i, m in enumerate(sorted_mods) if m.package_id == "base.mod")
        dep_idx = next(i for i, m in enumerate(sorted_mods) if m.package_id == "dependent.mod")
        self.assertLess(base_idx, dep_idx)


class TestModsConfigParser(unittest.TestCase):
    """Tests for ModsConfig.xml reading and writing."""
    
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.parser = ModsConfigParser()
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_write_mods_config_lowercase_ids(self):
        """Test that package IDs are written in lowercase."""
        active_mods = ["Test.Mod.ID", "Another.MOD"]
        self.parser.write_mods_config(self.temp_dir, active_mods)
        
        mods_config = self.temp_dir / "ModsConfig.xml"
        content = mods_config.read_text()
        self.assertIn("test.mod.id", content)
        self.assertIn("another.mod", content)
        self.assertNotIn("Test.Mod.ID", content)
        self.assertNotIn("Another.MOD", content)
    
    def test_write_mods_config_structure(self):
        """Test that ModsConfig.xml has correct structure."""
        active_mods = ["ludeon.rimworld", "test.mod"]
        self.parser.write_mods_config(self.temp_dir, active_mods)
        
        mods_config = self.temp_dir / "ModsConfig.xml"
        content = mods_config.read_text()
        
        self.assertIn("<ModsConfigData>", content)
        self.assertIn("<activeMods>", content)
        self.assertIn("<li>ludeon.rimworld</li>", content)
        self.assertIn("<li>test.mod</li>", content)
    
    def test_parse_mods_config(self):
        """Test reading existing ModsConfig.xml."""
        config_content = '''<?xml version="1.0" encoding="utf-8"?>
<ModsConfigData>
    <version>1.5.4104 rev435</version>
    <activeMods>
        <li>ludeon.rimworld</li>
        <li>brrainz.harmony</li>
        <li>test.mod</li>
    </activeMods>
    <knownExpansions>
        <li>ludeon.rimworld.royalty</li>
    </knownExpansions>
</ModsConfigData>'''
        
        mods_config = self.temp_dir / "ModsConfig.xml"
        mods_config.write_text(config_content)
        
        active_mods, version, expansions = self.parser.parse_mods_config(self.temp_dir)
        
        self.assertEqual(len(active_mods), 3)
        self.assertIn("ludeon.rimworld", active_mods)
        self.assertIn("brrainz.harmony", active_mods)
        self.assertIn("test.mod", active_mods)
        self.assertEqual(version, "1.5.4104 rev435")
        self.assertIn("ludeon.rimworld.royalty", expansions)
    
    def test_find_mods_config(self):
        """Test finding ModsConfig.xml in config folder."""
        mods_config = self.temp_dir / "ModsConfig.xml"
        mods_config.write_text("<ModsConfigData></ModsConfigData>")
        
        found = self.parser.find_mods_config(self.temp_dir)
        self.assertIsNotNone(found)
        self.assertEqual(found, mods_config)
    
    def test_find_mods_config_not_found(self):
        """Test finding ModsConfig.xml when it doesn't exist."""
        found = self.parser.find_mods_config(self.temp_dir)
        self.assertIsNone(found)


if __name__ == "__main__":
    unittest.main()
