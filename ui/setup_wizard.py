"""
Auto-Setup Wizard for RimModManager
First-run experience that auto-detects installations and helps install requirements.
"""

import logging
import subprocess
import sys
from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QTextEdit, QGroupBox, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from game_detector import GameDetector, RimWorldInstallation
from workshop_downloader import WorkshopDownloader

log = logging.getLogger("rimmodmanager.setup_wizard")


class SetupWorker(QThread):
    """Background worker for setup tasks."""
    progress = pyqtSignal(int, str)  # percentage, message
    finished = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, task: str, **kwargs):
        super().__init__()
        self.task = task
        self.kwargs = kwargs
    
    def run(self):
        try:
            if self.task == "detect_games":
                self._detect_games()
            elif self.task == "check_steamcmd":
                self._check_steamcmd()
            elif self.task == "install_steamcmd":
                self._install_steamcmd()
        except Exception as e:
            log.exception(f"Setup task failed: {self.task}")
            self.finished.emit(False, str(e))
    
    def _detect_games(self):
        self.progress.emit(10, "Scanning for RimWorld installations...")
        
        detector = GameDetector()
        self.progress.emit(50, "Checking Steam, GOG, Lutris, Bottles, Heroic...")
        
        installations = detector.detect_all()
        
        self.progress.emit(80, f"Found {len(installations)} installation(s)")
        
        if installations:
            self.progress.emit(100, "Detection complete!")
            self.finished.emit(True, f"Found {len(installations)} installation(s)")
        else:
            self.progress.emit(100, "No installations found")
            self.finished.emit(False, "No RimWorld installations detected")
    
    def _check_steamcmd(self):
        self.progress.emit(20, "Checking for SteamCMD...")
        
        downloader = WorkshopDownloader()
        
        if downloader.is_steamcmd_available():
            self.progress.emit(100, f"SteamCMD found: {downloader.steamcmd_path}")
            self.finished.emit(True, downloader.steamcmd_path)
        else:
            self.progress.emit(100, "SteamCMD not found")
            self.finished.emit(False, "")
    
    def _install_steamcmd(self):
        platform = sys.platform
        self.progress.emit(10, "Installing SteamCMD...")
        
        if platform.startswith('linux'):
            self._install_steamcmd_linux()
        elif platform == 'darwin':
            self._install_steamcmd_macos()
        elif platform.startswith('win'):
            self._install_steamcmd_windows()
        else:
            self.finished.emit(False, "Auto-install not supported on this platform")
    
    def _install_steamcmd_linux(self):
        """Install SteamCMD on Linux."""
        # Try apt first
        self.progress.emit(20, "Trying apt package manager...")
        try:
            result = subprocess.run(
                ["which", "apt"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                self.progress.emit(40, "Running: sudo apt install steamcmd")
                # We can't run sudo automatically, but we can try without sudo first
                result = subprocess.run(
                    ["apt", "install", "-y", "steamcmd"],
                    capture_output=True, text=True, timeout=60
                )
                if result.returncode == 0:
                    self.progress.emit(100, "SteamCMD installed via apt!")
                    self.finished.emit(True, "Installed via apt")
                    return
        except (subprocess.TimeoutExpired, OSError):
            pass
        
        # Try manual install
        self.progress.emit(50, "Downloading SteamCMD manually...")
        try:
            import urllib.request
            import tarfile
            
            steamcmd_dir = Path.home() / "steamcmd"
            steamcmd_dir.mkdir(exist_ok=True)
            
            archive_path = steamcmd_dir / "steamcmd_linux.tar.gz"
            
            self.progress.emit(60, "Downloading from Steam CDN...")
            urllib.request.urlretrieve(
                "https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz",
                archive_path
            )
            
            self.progress.emit(80, "Extracting...")
            with tarfile.open(archive_path, "r:gz") as tar:
                tar.extractall(path=steamcmd_dir)
            
            archive_path.unlink()
            
            # Make executable
            steamcmd_sh = steamcmd_dir / "steamcmd.sh"
            if steamcmd_sh.exists():
                steamcmd_sh.chmod(0o755)
            
            self.progress.emit(100, "SteamCMD installed to ~/steamcmd/")
            self.finished.emit(True, str(steamcmd_sh))
            
        except Exception as e:
            self.finished.emit(False, f"Manual install failed: {e}")
    
    def _install_steamcmd_windows(self):
        """Install SteamCMD on Windows via direct download."""
        import urllib.request
        import zipfile

        self.progress.emit(20, "Downloading SteamCMD...")
        try:
            steamcmd_dir = Path.home() / "steamcmd"
            steamcmd_dir.mkdir(exist_ok=True)

            zip_path = steamcmd_dir / "steamcmd.zip"
            self.progress.emit(40, "Downloading from Steam CDN...")
            urllib.request.urlretrieve(
                "https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip",
                zip_path
            )

            self.progress.emit(70, "Extracting...")
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(path=steamcmd_dir)
            zip_path.unlink()

            exe = steamcmd_dir / "steamcmd.exe"
            if not exe.exists():
                self.finished.emit(False, "steamcmd.exe not found after extraction")
                return

            self.progress.emit(85, "Running first-time update (steamcmd +quit)...")
            proc = subprocess.run(
                [str(exe), "+quit"],
                capture_output=True, text=True, timeout=120
            )
            if proc.returncode == 0:
                self.progress.emit(100, f"SteamCMD ready at {exe}")
                self.finished.emit(True, str(exe))
            else:
                self.finished.emit(False, f"SteamCMD update failed (exit code {proc.returncode})")
        except subprocess.TimeoutExpired:
            self.finished.emit(False, "SteamCMD update timed out (check internet)")
        except Exception as e:
            self.finished.emit(False, f"Windows install failed: {e}")

    def _install_steamcmd_macos(self):
        """Install SteamCMD on macOS."""
        self.progress.emit(20, "Trying Homebrew...")
        try:
            result = subprocess.run(
                ["which", "brew"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                self.progress.emit(50, "Running: brew install steamcmd")
                result = subprocess.run(
                    ["brew", "install", "steamcmd"],
                    capture_output=True, text=True, timeout=120
                )
                if result.returncode == 0:
                    self.progress.emit(100, "SteamCMD installed via Homebrew!")
                    self.finished.emit(True, "Installed via Homebrew")
                    return
        except (subprocess.TimeoutExpired, OSError):
            pass
        
        self.finished.emit(False, "Please install Homebrew first: https://brew.sh")


class SetupWizard(QDialog):
    """
    First-run setup wizard.
    Guides users through:
    1. Game detection
    2. SteamCMD installation (if needed)
    3. Final confirmation
    """
    
    setup_complete = pyqtSignal(list, str)  # installations, steamcmd_path
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("RimModManager - First-Time Setup")
        self.setMinimumSize(600, 500)
        self.setModal(True)
        
        self.installations: list[RimWorldInstallation] = []
        self.steamcmd_path: str = ""
        
        self._current_step = 0
        self._total_steps = 3
        
        self._setup_ui()
        self._start_step_1()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        self.header_label = QLabel("<h2>🚀 Welcome to RimModManager!</h2>")
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.header_label)
        
        self.step_label = QLabel("Setting up...")
        self.step_label.setStyleSheet("color: #666; font-size: 14px;")
        self.step_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.step_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # Content area
        self.content_frame = QFrame()
        self.content_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        self.content_layout = QVBoxLayout(self.content_frame)
        layout.addWidget(self.content_frame, 1)
        
        # Log output
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4; font-family: monospace;")
        self.log_text.setVisible(False)
        layout.addWidget(self.log_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.btn_back = QPushButton("← Back")
        self.btn_back.setEnabled(False)
        self.btn_back.clicked.connect(self._go_back)
        button_layout.addWidget(self.btn_back)
        
        button_layout.addStretch()
        
        self.btn_next = QPushButton("Next →")
        self.btn_next.clicked.connect(self._go_next)
        button_layout.addWidget(self.btn_next)
        
        self.btn_skip = QPushButton("Skip Setup")
        self.btn_skip.setStyleSheet("color: #666;")
        self.btn_skip.clicked.connect(self._skip_setup)
        button_layout.addWidget(self.btn_skip)
        
        layout.addLayout(button_layout)
    
    def _log(self, message: str):
        """Add message to log."""
        self.log_text.append(message)
        self.log_text.moveCursor(self.log_text.textCursor().MoveOperation.End)
    
    def _update_progress(self, step: int, message: str):
        """Update progress bar and step label."""
        self.progress_bar.setValue(step)
        self.step_label.setText(message)
    
    def _start_step_1(self):
        """Step 1: Detect RimWorld installations."""
        self._current_step = 1
        self._update_step_ui()
        
        # Clear content
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add detection info
        info = QLabel(
            "<p><b>Step 1: Finding RimWorld</b></p>"
            "<p>We'll scan your system for RimWorld installations.</p>"
            "<p style='color: #666;'>Checking: Steam, GOG, Lutris, Bottles, Heroic, and custom paths...</p>"
        )
        info.setWordWrap(True)
        self.content_layout.addWidget(info)
        
        # Start detection
        self.log_text.setVisible(True)
        self._log("Starting game detection...")
        
        self.worker = SetupWorker("detect_games")
        self.worker.progress.connect(self._on_detect_progress)
        self.worker.finished.connect(self._on_detect_finished)
        self.worker.start()
        
        self.btn_next.setEnabled(False)
    
    def _on_detect_progress(self, percent: int, message: str):
        """Handle detection progress."""
        self._update_progress(percent, message)
        self._log(message)
    
    def _on_detect_finished(self, success: bool, message: str):
        """Handle detection completion."""
        self._log(message)
        
        if success:
            # Get installations
            detector = GameDetector()
            self.installations = detector.detect_all()
            
            if self.installations:
                self._show_installation_results()
                self.btn_next.setEnabled(True)
            else:
                self._show_no_installation()
                self.btn_next.setEnabled(True)
        else:
            self._log(f"Detection failed: {message}")
            self.btn_next.setEnabled(True)
    
    def _show_installation_results(self):
        """Show detected installations."""
        # Clear previous results
        for i in reversed(range(self.content_layout.count())):
            widget = self.content_layout.itemAt(i).widget()
            if widget and widget != self.log_text:
                widget.deleteLater()
        
        # Add results
        result_label = QLabel(f"<h3>✅ Found {len(self.installations)} installation(s)!</h3>")
        self.content_layout.addWidget(result_label)
        
        for i, inst in enumerate(self.installations, 1):
            box = QGroupBox(f"{i}. {inst.install_type.value}")
            box_layout = QVBoxLayout(box)
            
            details = QLabel(
                f"<b>Path:</b> {inst.path}<br>"
                f"<b>Has Mods folder:</b> {'Yes' if inst.has_mods_folder else 'No'}<br>"
                f"<b>Has Data folder:</b> {'Yes' if inst.has_data_folder else 'No'}"
            )
            details.setWordWrap(True)
            box_layout.addWidget(details)
            
            self.content_layout.addWidget(box)
    
    def _show_no_installation(self):
        """Show message when no installation found."""
        for i in reversed(range(self.content_layout.count())):
            widget = self.content_layout.itemAt(i).widget()
            if widget and widget != self.log_text:
                widget.deleteLater()
        
        warning = QLabel(
            "<h3>⚠️ No RimWorld installation found</h3>"
            "<p>Don't worry! You can add it manually later.</p>"
            "<p style='color: #666;'>Click Next to continue setup.</p>"
        )
        warning.setWordWrap(True)
        self.content_layout.addWidget(warning)
    
    def _start_step_2(self):
        """Step 2: Check/install SteamCMD."""
        self._current_step = 2
        self._update_step_ui()
        
        # Clear content
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        info = QLabel(
            "<p><b>Step 2: SteamCMD Setup</b></p>"
            "<p>SteamCMD is required to download Workshop mods.</p>"
        )
        info.setWordWrap(True)
        self.content_layout.addWidget(info)
        
        self.log_text.setVisible(True)
        self._log("Checking for SteamCMD...")
        
        self.worker = SetupWorker("check_steamcmd")
        self.worker.progress.connect(self._on_steamcmd_progress)
        self.worker.finished.connect(self._on_steamcmd_finished)
        self.worker.start()
        
        self.btn_next.setEnabled(False)
    
    def _on_steamcmd_progress(self, percent: int, message: str):
        """Handle SteamCMD check progress."""
        self._update_progress(percent, message)
        self._log(message)
    
    def _on_steamcmd_finished(self, success: bool, message: str):
        """Handle SteamCMD check completion."""
        self._log(message)
        
        if success:
            self.steamcmd_path = message
            self._show_steamcmd_found()
        else:
            self._show_steamcmd_not_found()
        
        self.btn_next.setEnabled(True)
    
    def _show_steamcmd_found(self):
        """Show SteamCMD found message."""
        for i in reversed(range(self.content_layout.count())):
            widget = self.content_layout.itemAt(i).widget()
            if widget and widget != self.log_text:
                widget.deleteLater()
        
        result = QLabel(f"<h3>✅ SteamCMD found!</h3><p>Path: {self.steamcmd_path}</p>")
        result.setWordWrap(True)
        self.content_layout.addWidget(result)
    
    def _show_steamcmd_not_found(self):
        """Show SteamCMD not found with install option."""
        for i in reversed(range(self.content_layout.count())):
            widget = self.content_layout.itemAt(i).widget()
            if widget and widget != self.log_text:
                widget.deleteLater()
        
        warning = QLabel(
            "<h3>⚠️ SteamCMD not found</h3>"
            "<p>Workshop mod downloads won't work without it.</p>"
        )
        warning.setWordWrap(True)
        self.content_layout.addWidget(warning)
        
        # Install button
        self.btn_install_steamcmd = QPushButton("🔧 Install SteamCMD Automatically")
        self.btn_install_steamcmd.setStyleSheet("background-color: #2a6a2a; color: white; font-weight: bold; padding: 8px;")
        self.btn_install_steamcmd.clicked.connect(self._install_steamcmd)
        self.content_layout.addWidget(self.btn_install_steamcmd)
        
        # Manual instructions
        manual = QLabel(
            "<p><b>Or install manually:</b></p>"
            "<pre style='background: #2d2d2d; color: #e0e0e0; padding: 10px; border-radius: 4px; font-family: monospace;'>"
            "Ubuntu/Debian: sudo apt install steamcmd\n"
            "Arch:          yay -S steamcmd\n"
            "Fedora:        sudo dnf install steamcmd</pre>"
        )
        manual.setWordWrap(True)
        self.content_layout.addWidget(manual)
    
    def _install_steamcmd(self):
        """Install SteamCMD automatically."""
        self.btn_install_steamcmd.setEnabled(False)
        self._log("Starting automatic SteamCMD installation...")
        
        self.worker = SetupWorker("install_steamcmd")
        self.worker.progress.connect(self._on_install_progress)
        self.worker.finished.connect(self._on_install_finished)
        self.worker.start()
    
    def _on_install_progress(self, percent: int, message: str):
        """Handle SteamCMD install progress."""
        self._update_progress(percent, message)
        self._log(message)
    
    def _on_install_finished(self, success: bool, message: str):
        """Handle SteamCMD install completion."""
        self._log(message)
        
        if success:
            self.steamcmd_path = message
            self._log(f"✅ SteamCMD installed at: {message}")
        else:
            self._log(f"❌ Installation failed: {message}")
        
        self.btn_install_steamcmd.setEnabled(True)
    
    def _start_step_3(self):
        """Step 3: Summary and finish."""
        self._current_step = 3
        self._update_step_ui()
        
        # Clear content
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        summary = QLabel("<h3>📋 Setup Summary</h3>")
        self.content_layout.addWidget(summary)
        
        # Game installations
        game_box = QGroupBox("RimWorld Installations")
        game_layout = QVBoxLayout(game_box)
        
        if self.installations:
            for inst in self.installations:
                label = QLabel(f"• {inst.install_type.value}: {inst.path}")
                label.setWordWrap(True)
                game_layout.addWidget(label)
        else:
            game_layout.addWidget(QLabel("• None detected (you can add manually later)"))
        
        self.content_layout.addWidget(game_box)
        
        # SteamCMD
        steamcmd_box = QGroupBox("SteamCMD")
        steamcmd_layout = QVBoxLayout(steamcmd_box)
        
        if self.steamcmd_path:
            steamcmd_layout.addWidget(QLabel(f"• Installed: {self.steamcmd_path}"))
        else:
            steamcmd_layout.addWidget(QLabel("• Not installed (Workshop downloads unavailable)"))
        
        self.content_layout.addWidget(steamcmd_box)
        
        # Finish message
        finish_msg = QLabel(
            "<p style='color: #666;'>Click <b>Finish</b> to start using RimModManager!</p>"
            "<p style='color: #666;'>You can always change settings later.</p>"
        )
        finish_msg.setWordWrap(True)
        self.content_layout.addWidget(finish_msg)
        
        self._update_progress(100, "Setup complete!")
        self.btn_next.setText("✓ Finish")
    
    def _update_step_ui(self):
        """Update UI for current step."""
        self.step_label.setText(f"Step {self._current_step} of {self._total_steps}")
        self.btn_back.setEnabled(self._current_step > 1)
        
        if self._current_step == self._total_steps:
            self.btn_next.setText("✓ Finish")
            self.btn_skip.setVisible(False)
        else:
            self.btn_next.setText("Next →")
            self.btn_skip.setVisible(True)
    
    def _go_next(self):
        """Go to next step or finish."""
        if self._current_step < self._total_steps:
            if self._current_step == 1:
                self._start_step_2()
            elif self._current_step == 2:
                self._start_step_3()
        else:
            self._finish_setup()
    
    def _go_back(self):
        """Go to previous step."""
        if self._current_step > 1:
            if self._current_step == 2:
                self._start_step_1()
            elif self._current_step == 3:
                self._start_step_2()
    
    def _skip_setup(self):
        """Skip setup and go to main window."""
        self.setup_complete.emit([], "")
        self.accept()
    
    def _finish_setup(self):
        """Finish setup and emit results."""
        self.setup_complete.emit(self.installations, self.steamcmd_path)
        self.accept()
