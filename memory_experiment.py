#!/usr/bin/env python3
"""
Memory usage experiments for RimModManager.
Tests different approaches to minimize RAM usage.
"""

import os
import sys
import subprocess
import resource

def get_memory_mb():
    """Get current process memory usage in MB."""
    try:
        # Linux
        with open(f'/proc/{os.getpid()}/status', 'r') as f:
            for line in f:
                if line.startswith('VmRSS:'):
                    return int(line.split()[1]) / 1024  # kB to MB
    except (FileNotFoundError, IndexError):
        pass
    # Fallback
    ru = resource.getrusage(resource.RUSAGE_SELF)
    return ru.ru_maxrss / 1024  # macOS uses bytes, Linux uses kB

def measure_import(module_name, description):
    """Measure memory before and after importing a module."""
    # Import in a fresh subprocess for accurate measurement
    code = f"""
import os, sys, resource
before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
try:
    {module_name}
except Exception:
    pass
import gc
gc.collect()
after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
print(f"{{after - before:.1f}}")
"""
    result = subprocess.run(
        [sys.executable, '-c', code],
        capture_output=True, text=True, timeout=30
    )
    
    try:
        mem_delta = float(result.stdout.strip())
    except (ValueError, AttributeError):
        mem_delta = 0
    
    return mem_delta

def experiment_1_baseline():
    """Measure baseline PyQt6 import."""
    print("=" * 60)
    print("Experiment 1: Baseline PyQt6 memory usage")
    print("=" * 60)
    
    code = """
import os, sys, resource
before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
from PyQt6.QtWidgets import QApplication
app = QApplication([])
import gc; gc.collect()
after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
print(f"PyQt6 base: {after - before:.1f} MB")
"""
    result = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True, timeout=30)
    print(result.stdout.strip())
    print()

def experiment_2_webengine():
    """Measure WebEngine memory impact."""
    print("=" * 60)
    print("Experiment 2: WebEngine memory impact")
    print("=" * 60)
    
    # Without WebEngine
    code1 = """
import os, sys, resource
before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
from PyQt6.QtWidgets import QApplication
app = QApplication([])
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette, QColor
import gc; gc.collect()
after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
print(f"Without WebEngine: {after - before:.1f} MB")
"""
    result1 = subprocess.run([sys.executable, '-c', code1], capture_output=True, text=True, timeout=30)
    print(result1.stdout.strip())
    
    # With WebEngine
    code2 = """
import os, sys, resource
before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
from PyQt6.QtWidgets import QApplication
app = QApplication([])
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette, QColor
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebEngineCore import QWebEngineSettings, QWebEngineProfile
except ImportError:
    pass
import gc; gc.collect()
after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
print(f"With WebEngine import: {after - before:.1f} MB")
"""
    result2 = subprocess.run([sys.executable, '-c', code2], capture_output=True, text=True, timeout=30)
    print(result2.stdout.strip())
    print()

def experiment_3_lazy_import():
    """Test lazy import approach."""
    print("=" * 60)
    print("Experiment 3: Lazy import vs eager import")
    print("=" * 60)
    
    # Eager import
    code_eager = """
import os, sys, resource
before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
from PyQt6.QtWidgets import QApplication
app = QApplication([])
# Import everything upfront
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings, QWebEngineProfile
import gc; gc.collect()
after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
print(f"Eager: {after - before:.1f} MB")
"""
    result_eager = subprocess.run([sys.executable, '-c', code_eager], capture_output=True, text=True, timeout=30)
    print(f"Eager import: {result_eager.stdout.strip()}")
    
    # Lazy import
    code_lazy = """
import os, sys, resource
before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
from PyQt6.QtWidgets import QApplication
app = QApplication([])
# Don't import WebEngine until needed
import gc; gc.collect()
after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
print(f"Lazy (before WebEngine): {after - before:.1f} MB")
# Now import WebEngine
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebEngineCore import QWebEngineSettings, QWebEngineProfile
except ImportError:
    pass
import gc; gc.collect()
after2 = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
print(f"Lazy (after WebEngine): {after2 - before:.1f} MB")
"""
    result_lazy = subprocess.run([sys.executable, '-c', code_lazy], capture_output=True, text=True, timeout=30)
    print(result_lazy.stdout.strip())
    print()

def experiment_4_qtextbrowser():
    """Test QTextBrowser as lightweight fallback."""
    print("=" * 60)
    print("Experiment 4: QTextBrowser vs QLabel memory")
    print("=" * 60)
    
    # QLabel approach
    code_label = """
import os, sys, resource
before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
from PyQt6.QtWidgets import QApplication, QLabel
app = QApplication([])
label = QLabel("Test")
import gc; gc.collect()
after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
print(f"QLabel: {after - before:.1f} MB")
"""
    result_label = subprocess.run([sys.executable, '-c', code_label], capture_output=True, text=True, timeout=30)
    print(f"QLabel: {result_label.stdout.strip()}")
    
    # QTextBrowser approach
    code_browser = """
import os, sys, resource
before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
from PyQt6.QtWidgets import QApplication, QTextBrowser
app = QApplication([])
browser = QTextBrowser()
browser.setOpenExternalLinks(True)
browser.setHtml("<h1>Workshop Browser</h1><p>Click links to open in system browser</p>")
import gc; gc.collect()
after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
print(f"QTextBrowser: {after - before:.1f} MB")
"""
    result_browser = subprocess.run([sys.executable, '-c', code_browser], capture_output=True, text=True, timeout=30)
    print(f"QTextBrowser: {result_browser.stdout.strip()}")
    print()

def experiment_5_full_app():
    """Measure full app startup memory."""
    print("=" * 60)
    print("Experiment 5: Full app startup memory")
    print("=" * 60)
    
    # Test importing main modules
    code = """
import os, sys, resource
before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024

# Simulate app startup
from PyQt6.QtWidgets import QApplication
app = QApplication([])

# Import core modules
sys.path.insert(0, '/tmp/RimModManager-gh')
from config_handler import ConfigHandler
from game_detector import GameDetector
from mod_parser import ModParser

# DON'T import WebEngine yet
import gc; gc.collect()
after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
print(f"Core app (no WebEngine): {after - before:.1f} MB")

# Now import WebEngine (lazy)
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebEngineCore import QWebEngineSettings, QWebEngineProfile
except ImportError:
    pass
import gc; gc.collect()
after2 = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
print(f"After WebEngine import: {after2 - before:.1f} MB")
"""
    result = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True, timeout=30)
    print(result.stdout.strip())
    print()

if __name__ == '__main__':
    print("🧪 RimModManager Memory Experiments")
    print("=" * 60)
    print()
    
    experiment_1_baseline()
    experiment_2_webengine()
    experiment_3_lazy_import()
    experiment_4_qtextbrowser()
    experiment_5_full_app()
    
    print("=" * 60)
    print("✅ Experiments complete!")
