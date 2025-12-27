#!/usr/bin/env python3
"""
Unit tests for mod_importer.py
Tests import functionality for various modlist formats.
"""

import unittest
import tempfile
import shutil
import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from mod_importer import ModImporter, ImportFormat, ImportResult


class TestModImporter(unittest.TestCase):
    """Tests for ModImporter class."""
    
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.importer = ModImporter()
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_detect_format_json(self):
        """Test JSON format detection."""
        json_file = self.temp_dir / "modlist.json"
        json_file.write_text('{"mods": ["mod.one"]}')
        
        fmt = self.importer.detect_format(json_file)
        self.assertEqual(fmt, ImportFormat.RIMSORT_JSON)
    
    def test_detect_format_modsconfig(self):
        """Test ModsConfig.xml detection."""
        xml_file = self.temp_dir / "ModsConfig.xml"
        xml_file.write_text('<ModsConfigData><activeMods></activeMods></ModsConfigData>')
        
        fmt = self.importer.detect_format(xml_file)
        self.assertEqual(fmt, ImportFormat.MODSCONFIG_XML)
    
    def test_detect_format_plain_text(self):
        """Test plain text format detection."""
        txt_file = self.temp_dir / "mods.txt"
        txt_file.write_text("mod.one\nmod.two\nmod.three")
        
        fmt = self.importer.detect_format(txt_file)
        self.assertEqual(fmt, ImportFormat.PLAIN_TEXT)
    
    def test_detect_format_workshop_ids(self):
        """Test workshop IDs format detection."""
        txt_file = self.temp_dir / "workshop.txt"
        txt_file.write_text("123456789\n987654321\n111222333")
        
        fmt = self.importer.detect_format(txt_file)
        self.assertEqual(fmt, ImportFormat.WORKSHOP_IDS)
    
    def test_detect_format_nonexistent(self):
        """Test format detection for non-existent file."""
        fake_file = self.temp_dir / "nonexistent.json"
        fmt = self.importer.detect_format(fake_file)
        self.assertEqual(fmt, ImportFormat.UNKNOWN)
    
    def test_import_rimsort_json(self):
        """Test importing RimSort JSON format."""
        json_file = self.temp_dir / "rimsort.json"
        data = {
            "name": "Test Modlist",
            "mods": ["mod.one", "mod.two", "mod.three"]
        }
        json_file.write_text(json.dumps(data))
        
        result = self.importer.import_file(json_file)
        
        self.assertTrue(result.success)
        self.assertEqual(result.format_detected, ImportFormat.RIMSORT_JSON)
        self.assertEqual(len(result.package_ids), 3)
        self.assertIn("mod.one", result.package_ids)
    
    def test_import_modsconfig_xml(self):
        """Test importing ModsConfig.xml format."""
        xml_file = self.temp_dir / "ModsConfig.xml"
        xml_content = '''<?xml version="1.0" encoding="utf-8"?>
<ModsConfigData>
    <activeMods>
        <li>ludeon.rimworld</li>
        <li>brrainz.harmony</li>
        <li>test.mod</li>
    </activeMods>
</ModsConfigData>'''
        xml_file.write_text(xml_content)
        
        result = self.importer.import_file(xml_file)
        
        self.assertTrue(result.success)
        self.assertEqual(result.format_detected, ImportFormat.MODSCONFIG_XML)
        self.assertEqual(len(result.package_ids), 3)
        self.assertIn("ludeon.rimworld", result.package_ids)
    
    def test_import_plain_text(self):
        """Test importing plain text package IDs."""
        txt_file = self.temp_dir / "mods.txt"
        txt_file.write_text("mod.one\nmod.two\n# comment\nmod.three")
        
        result = self.importer.import_file(txt_file)
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.package_ids), 3)
    
    def test_import_workshop_ids(self):
        """Test importing workshop IDs."""
        txt_file = self.temp_dir / "workshop.txt"
        txt_file.write_text("123456789\n987654321")
        
        result = self.importer.import_file(txt_file)
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.workshop_ids), 2)
        self.assertIn("123456789", result.workshop_ids)
    
    def test_import_from_text(self):
        """Test importing from pasted text."""
        text = """mod.one
mod.two
123456789
https://steamcommunity.com/sharedfiles/filedetails/?id=987654321"""
        
        result = self.importer.import_from_text(text)
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.package_ids), 2)
        self.assertEqual(len(result.workshop_ids), 2)
    
    def test_import_empty_file(self):
        """Test importing empty file."""
        txt_file = self.temp_dir / "empty.txt"
        txt_file.write_text("")
        
        result = self.importer.import_file(txt_file)
        
        self.assertFalse(result.success)
    
    def test_import_invalid_json(self):
        """Test importing invalid JSON."""
        json_file = self.temp_dir / "invalid.json"
        json_file.write_text("not valid json {{{")
        
        result = self.importer.import_file(json_file)
        
        self.assertFalse(result.success)
        self.assertTrue(len(result.errors) > 0)


class TestImportResult(unittest.TestCase):
    """Tests for ImportResult dataclass."""
    
    def test_import_result_creation(self):
        """Test creating ImportResult."""
        result = ImportResult(
            success=True,
            format_detected=ImportFormat.PLAIN_TEXT,
            package_ids=["mod.one"],
            workshop_ids=["123"],
            mod_names={"mod.one": "Test Mod"},
            errors=[],
            warnings=[]
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.format_detected, ImportFormat.PLAIN_TEXT)
        self.assertEqual(len(result.package_ids), 1)


class TestImportFormat(unittest.TestCase):
    """Tests for ImportFormat enum."""
    
    def test_all_formats_have_values(self):
        """Test that all formats have string values."""
        for fmt in ImportFormat:
            self.assertIsInstance(fmt.value, str)
            self.assertTrue(len(fmt.value) > 0)


if __name__ == "__main__":
    unittest.main()
