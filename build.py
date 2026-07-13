"""
Build Script for RimModManager
Creates standalone executables for Linux, Windows, and macOS using PyInstaller.
"""

import PyInstaller.__main__
import sys
import shutil
from pathlib import Path


def get_platform():
    """Detect current platform."""
    if sys.platform.startswith('win') or sys.platform in ('cygwin', 'msys'):
        return 'windows'
    elif sys.platform == 'darwin':
        return 'darwin'
    else:
        return 'linux'


def _convert_svg_to_ico(svg_path: Path, ico_path: Path):
    """Convert SVG to Windows ICO using PyQt6."""
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtGui import QPixmap, QPainter
        from PyQt6.QtSvg import QSvgRenderer
        from PyQt6.QtCore import QByteArray
        import sys

        app = QApplication(sys.argv)
        svg_data = svg_path.read_bytes()
        renderer = QSvgRenderer(QByteArray(svg_data))
        pixmap = QPixmap(256, 256)
        pixmap.fill()
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        pixmap.save(str(ico_path), 'ICO')
        print(f"✅ Generated {ico_path.name}")
    except ImportError:
        print("⚠️ PyQt6 not available, skipping icon conversion")


def build():
    platform = get_platform()
    print(f"🚀 Starting build for {platform}...")
    
    # Clean previous builds
    for d in ['build', 'dist']:
        if Path(d).exists():
            shutil.rmtree(d)
    
    # Core PyInstaller arguments
    args = [
        'main.py',
        '--name=RimModManager',
        '--noconfirm',
        '--onefile',
        '--windowed',
        '--clean',
        '--strip',
        '--optimize=2',
    ]
    
    # Icon - platform specific
    icon_svg = Path('resources/icon.svg')
    if icon_svg.exists():
        if platform == 'windows':
            ico_path = Path('resources/icon.ico')
            if not ico_path.exists():
                _convert_svg_to_ico(icon_svg, ico_path)
            if ico_path.exists():
                args.append(f'--icon={ico_path}')
        elif platform == 'darwin':
            icns_paths = [
                Path('resources/icon.icns'),
                Path('resources/RimModManager.icns'),
            ]
            found_icns = next((p for p in icns_paths if p.exists()), None)
            if found_icns:
                args.append(f'--icon={found_icns}')
        else:
            args.append(f'--icon={icon_svg}')
    
    # Exclude heavy/unused libraries
    excludes = [
        'PyQt6.QtWebEngine',
        'PyQt6.QtWebEngineCore',
        'PyQt6.QtWebEngineWidgets',
        'PyQt6.QtNetwork',
        'tkinter',
        'unittest',
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
    
    # Add data files - use correct separator for platform
    data_sep = ';' if platform == 'windows' else ':'
    if Path('resources').exists():
        args.append(f'--add-data=resources{data_sep}resources')
    
    # Collect all PyQt6 modules we actually use
    args.append('--collect-submodules=PyQt6.QtWidgets')
    args.append('--collect-submodules=PyQt6.QtCore')
    args.append('--collect-submodules=PyQt6.QtGui')
    
    # Try UPX (Windows only for best compatibility)
    try:
        if platform == 'windows' and shutil.which('upx'):
            print("✨ UPX found! Compression enabled.")
            args.append('--upx-dir=' + str(Path(shutil.which('upx')).parent))
        else:
            print("ℹ️ UPX not used (Linux/macOS have compatibility issues).")
    except (ImportError, OSError):
        pass
    
    print(f"📦 Building with {len(excludes)} exclusions...")
    print(f"Args: {args}")
    
    try:
        PyInstaller.__main__.run(args)
        print("\n✅ Build complete!")
        
        # Check size
        if platform == 'windows':
            dist_path = Path("dist/RimModManager.exe")
        else:
            dist_path = Path("dist/RimModManager")
        
        if dist_path.exists():
            size_mb = dist_path.stat().st_size / (1024 * 1024)
            print(f"📄 Output size: {size_mb:.2f} MB")
            
            # Rename for platform if needed
            if platform == 'windows':
                target_name = "RimModManager-Windows-x64.exe"
            elif platform == 'darwin':
                target_name = "RimModManager-macOS-x64"
            else:
                target_name = "RimModManager-Linux-x64"
            
            target_path = Path("dist") / target_name
            if dist_path.name != target_name:
                dist_path.rename(target_path)
                print(f"📦 Renamed to: {target_name}")
        else:
            print(f"⚠️ Output not found at {dist_path}")
            print("Contents of dist/:")
            for f in Path("dist").iterdir():
                print(f"  {f.name} ({f.stat().st_size / (1024*1024):.2f} MB)")
                
    except (RuntimeError, OSError, ImportError) as e:
        print(f"\n❌ Build failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    build()
