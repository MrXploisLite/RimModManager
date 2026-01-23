"""
Build Script for RimModManager (Lightweight Version)
Creates a standalone executable under 70MB by excluding heavy dependencies.
"""

import PyInstaller.__main__
import os
import shutil
from pathlib import Path

def build():
    print("🚀 Starting optimized build...")
    
    # Clean previous builds
    if Path("build").exists():
        shutil.rmtree("build")
    if Path("dist").exists():
        shutil.rmtree("dist")

    # Core PyInstaller arguments
    args = [
        'main.py',                        # Entry point
        '--name=RimModManager',           # Executable name
        '--noconfirm',                    # Overwrite output
        '--onefile',                      # Single executable
        '--windowed',                     # No console window
        '--clean',                        # Clean cache
        '--strip',                        # Strip symbols
        '--optimize=2',                   # Python optimization level
    ]

    # Exclude heavy libraries (WebEngine is biggest culprit)
    excludes = [
        'PyQt6.QtWebEngine',
        'PyQt6.QtWebEngineCore',
        'PyQt6.QtWebEngineWidgets',
        'PyQt6.QtNetwork',  # Only if not used elsewhere, but we use urllib
        'tkinter',
        'unittest',
        'email',
        'html',
        'http',
        'xml.sax',
        'xml.dom.pulldom',
        'pydoc',
        'pdb',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
    ]
    
    for lib in excludes:
        args.append(f'--exclude-module={lib}')

    # Add data files if needed
    if Path('resources').exists():
        args.append('--add-data=resources;resources')
    
    # Try to use UPX if available
    try:
        import shutil
        if shutil.which('upx'):
            print("✨ UPX found! Compression enabled.")
            args.append('--upx-dir=' + str(Path(shutil.which('upx')).parent))
        else:
            print("ℹ️ UPX not found. Install UPX for smaller executable size.")
    except Exception:
        pass

    print(f"📦 Building with {len(excludes)} exclusions...")
    
    try:
        PyInstaller.__main__.run(args)
        print("\n✅ Build complete!")
        
        # Check size
        dist_path = Path("dist/RimModManager.exe")
        if dist_path.exists():
            size_mb = dist_path.stat().st_size / (1024 * 1024)
            print(f"📄 Output size: {size_mb:.2f} MB")
            
            if size_mb < 70:
                print("🎉 SUCCESS: Target size < 70MB achieved!")
            else:
                print("⚠️ WARNING: Size exceeds 70MB target.")
                
    except Exception as e:
        print(f"\n❌ Build failed: {e}")

if __name__ == "__main__":
    build()
