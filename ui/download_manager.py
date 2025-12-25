"""
Download Manager with Live Logging for RimWorld Mod Manager
Provides real-time SteamCMD output and download progress.
"""

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Callable
from enum import Enum

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QProgressBar, QGroupBox, QScrollArea, QFrame,
    QSplitter, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QProcess, QTimer
from PyQt6.QtGui import QFont, QTextCursor, QColor


class DownloadStatus(Enum):
    PENDING = "Pending"
    DOWNLOADING = "Downloading"
    EXTRACTING = "Extracting"
    COMPLETE = "Complete"
    FAILED = "Failed"
    CANCELLED = "Cancelled"


@dataclass
class DownloadItem:
    """A single download item."""
    workshop_id: str
    name: str = ""
    status: DownloadStatus = DownloadStatus.PENDING
    progress: int = 0
    error: str = ""


class SteamCMDChecker:
    """Utility to check and help install SteamCMD."""
    
    @staticmethod
    def find_steamcmd() -> Optional[str]:
        """Find SteamCMD executable."""
        paths = [
            "steamcmd",
            "/usr/bin/steamcmd",
            "/usr/games/steamcmd",
            str(Path.home() / "steamcmd/steamcmd.sh"),
            str(Path.home() / ".local/share/Steam/steamcmd/steamcmd.sh"),
        ]
        
        for path in paths:
            if shutil.which(path):
                return path
            if Path(path).exists():
                return path
        return None
    
    @staticmethod
    def is_available() -> bool:
        """Check if SteamCMD is available."""
        return SteamCMDChecker.find_steamcmd() is not None
    
    @staticmethod
    def get_install_command() -> str:
        """Get the install command for the current system."""
        # Check for AUR helpers
        if shutil.which("yay"):
            return "yay -S steamcmd"
        elif shutil.which("paru"):
            return "paru -S steamcmd"
        elif shutil.which("pamac"):
            return "pamac build steamcmd"
        else:
            return "git clone https://aur.archlinux.org/steamcmd.git && cd steamcmd && makepkg -si"


class LiveDownloadWorker(QThread):
    """
    Download worker with live output streaming.
    Emits real-time SteamCMD output to the UI.
    """
    
    # Signals
    log_output = pyqtSignal(str)  # Real-time log line
    item_started = pyqtSignal(str)  # workshop_id
    item_progress = pyqtSignal(str, int)  # workshop_id, progress %
    item_complete = pyqtSignal(str, str)  # workshop_id, output_path
    item_failed = pyqtSignal(str, str)  # workshop_id, error
    all_complete = pyqtSignal(int, int)  # success_count, fail_count
    
    RIMWORLD_APPID = "294100"
    
    def __init__(self, steamcmd_path: str, workshop_ids: list[str], download_path: Path):
        super().__init__()
        self.steamcmd_path = steamcmd_path
        self.workshop_ids = workshop_ids
        self.download_path = download_path
        self._cancelled = False
    
    def cancel(self):
        """Cancel the download."""
        self._cancelled = True
    
    def run(self):
        success = 0
        failed = 0
        
        self.download_path.mkdir(parents=True, exist_ok=True)
        
        for wid in self.workshop_ids:
            if self._cancelled:
                self.log_output.emit(f"[CANCELLED] Download cancelled by user")
                break
            
            self.item_started.emit(wid)
            self.log_output.emit(f"\n{'='*50}")
            self.log_output.emit(f"[DOWNLOAD] Starting download: {wid}")
            self.log_output.emit(f"{'='*50}\n")
            
            result = self._download_single(wid)
            
            if result:
                success += 1
                self.item_complete.emit(wid, str(result))
                self.log_output.emit(f"\n[SUCCESS] Downloaded {wid} -> {result}\n")
            else:
                failed += 1
                self.item_failed.emit(wid, "Download failed")
                self.log_output.emit(f"\n[FAILED] Could not download {wid}\n")
        
        self.all_complete.emit(success, failed)
    
    def _download_single(self, workshop_id: str) -> Optional[Path]:
        """Download a single mod with live output."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            cmd = [
                self.steamcmd_path,
                "+force_install_dir", str(temp_path),
                "+login", "anonymous",
                "+workshop_download_item", self.RIMWORLD_APPID, workshop_id,
                "+quit"
            ]
            
            self.log_output.emit(f"[CMD] {' '.join(cmd)}\n")
            
            try:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
                
                # Stream output
                for line in process.stdout:
                    line = line.rstrip()
                    if line:
                        self.log_output.emit(f"  {line}")
                        
                        # Parse progress
                        if "Downloading" in line or "downloading" in line:
                            match = re.search(r'(\d+(?:\.\d+)?)\s*%', line)
                            if match:
                                progress = int(float(match.group(1)))
                                self.item_progress.emit(workshop_id, progress)
                        elif "Success" in line:
                            self.item_progress.emit(workshop_id, 100)
                    
                    if self._cancelled:
                        process.terminate()
                        return None
                
                process.wait()
                
                if process.returncode != 0:
                    self.log_output.emit(f"[ERROR] SteamCMD exited with code {process.returncode}")
                    return None
                
                # Find and move downloaded mod
                workshop_content = temp_path / "steamapps/workshop/content" / self.RIMWORLD_APPID / workshop_id
                
                if not workshop_content.exists():
                    self.log_output.emit(f"[ERROR] Mod folder not found at {workshop_content}")
                    return None
                
                # Move to final location
                final_path = self.download_path / workshop_id
                if final_path.exists():
                    shutil.rmtree(final_path)
                
                shutil.move(str(workshop_content), str(final_path))
                return final_path
                
            except Exception as e:
                self.log_output.emit(f"[EXCEPTION] {e}")
                return None


class DownloadLogWidget(QWidget):
    """
    Widget showing live download progress and logs.
    """
    
    download_complete = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._worker: Optional[LiveDownloadWorker] = None
        self._items: dict[str, DownloadItem] = {}
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header = QHBoxLayout()
        self.title_label = QLabel("📥 Download Manager")
        self.title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        header.addWidget(self.title_label)
        header.addStretch()
        
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #888;")
        header.addWidget(self.status_label)
        layout.addLayout(header)
        
        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Splitter for queue and log
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Download queue
        queue_group = QGroupBox("Download Queue")
        queue_layout = QVBoxLayout(queue_group)
        queue_layout.setContentsMargins(4, 4, 4, 4)
        
        self.queue_list = QListWidget()
        self.queue_list.setMaximumHeight(150)
        queue_layout.addWidget(self.queue_list)
        
        splitter.addWidget(queue_group)
        
        # Live log
        log_group = QGroupBox("Live Log (SteamCMD Output)")
        log_layout = QVBoxLayout(log_group)
        log_layout.setContentsMargins(4, 4, 4, 4)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("monospace", 9))
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #333;
            }
        """)
        log_layout.addWidget(self.log_text)
        
        splitter.addWidget(log_group)
        splitter.setSizes([150, 300])
        
        layout.addWidget(splitter, 1)
        
        # Controls
        controls = QHBoxLayout()
        
        self.btn_cancel = QPushButton("❌ Cancel")
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self._cancel_downloads)
        controls.addWidget(self.btn_cancel)
        
        self.btn_clear = QPushButton("🗑️ Clear Log")
        self.btn_clear.clicked.connect(self._clear_log)
        controls.addWidget(self.btn_clear)
        
        controls.addStretch()
        
        self.btn_close = QPushButton("✓ Done")
        self.btn_close.clicked.connect(lambda: self.download_complete.emit())
        controls.addWidget(self.btn_close)
        
        layout.addLayout(controls)
    
    def start_downloads(self, steamcmd_path: str, workshop_ids: list[str], download_path: Path):
        """Start downloading mods with live logging."""
        if self._worker and self._worker.isRunning():
            return
        
        # Clear previous state
        self.queue_list.clear()
        self._items.clear()
        
        # Add items to queue
        for wid in workshop_ids:
            item = DownloadItem(workshop_id=wid, name=f"Mod {wid}")
            self._items[wid] = item
            
            list_item = QListWidgetItem(f"⏳ {wid} - Pending")
            list_item.setData(Qt.ItemDataRole.UserRole, wid)
            self.queue_list.addItem(list_item)
        
        # Setup progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(workshop_ids))
        self.progress_bar.setValue(0)
        
        self.status_label.setText(f"Downloading 0/{len(workshop_ids)}...")
        self.btn_cancel.setEnabled(True)
        
        # Start worker
        self._worker = LiveDownloadWorker(steamcmd_path, workshop_ids, download_path)
        self._worker.log_output.connect(self._on_log)
        self._worker.item_started.connect(self._on_item_started)
        self._worker.item_progress.connect(self._on_item_progress)
        self._worker.item_complete.connect(self._on_item_complete)
        self._worker.item_failed.connect(self._on_item_failed)
        self._worker.all_complete.connect(self._on_all_complete)
        self._worker.start()
        
        self._log_info("Download manager started...")
    
    def _on_log(self, line: str):
        """Handle log output."""
        # Color code the output
        if "[ERROR]" in line or "[EXCEPTION]" in line or "[FAILED]" in line:
            self.log_text.setTextColor(QColor("#ff6b6b"))
        elif "[SUCCESS]" in line:
            self.log_text.setTextColor(QColor("#69db7c"))
        elif "[CMD]" in line or "[DOWNLOAD]" in line:
            self.log_text.setTextColor(QColor("#74c0fc"))
        elif line.startswith("="):
            self.log_text.setTextColor(QColor("#ffd43b"))
        else:
            self.log_text.setTextColor(QColor("#d4d4d4"))
        
        self.log_text.append(line)
        
        # Auto-scroll
        self.log_text.moveCursor(QTextCursor.MoveOperation.End)
    
    def _log_info(self, msg: str):
        """Log an info message."""
        self.log_text.setTextColor(QColor("#74c0fc"))
        self.log_text.append(f"[INFO] {msg}")
    
    def _on_item_started(self, workshop_id: str):
        """Handle item download started."""
        self._update_queue_item(workshop_id, "⬇️", "Downloading...")
    
    def _on_item_progress(self, workshop_id: str, progress: int):
        """Handle item progress."""
        self._update_queue_item(workshop_id, "⬇️", f"Downloading... {progress}%")
    
    def _on_item_complete(self, workshop_id: str, path: str):
        """Handle item complete."""
        self._update_queue_item(workshop_id, "✅", "Complete")
        self.progress_bar.setValue(self.progress_bar.value() + 1)
        
        done = self.progress_bar.value()
        total = self.progress_bar.maximum()
        self.status_label.setText(f"Downloaded {done}/{total}...")
    
    def _on_item_failed(self, workshop_id: str, error: str):
        """Handle item failed."""
        self._update_queue_item(workshop_id, "❌", f"Failed: {error}")
        self.progress_bar.setValue(self.progress_bar.value() + 1)
    
    def _on_all_complete(self, success: int, failed: int):
        """Handle all downloads complete."""
        self.btn_cancel.setEnabled(False)
        self.progress_bar.setVisible(False)
        
        self.status_label.setText(f"Complete: {success} succeeded, {failed} failed")
        self._log_info(f"All downloads complete: {success} succeeded, {failed} failed")
        
        if success > 0:
            self._log_info("Mods are ready! Switch to Mod Manager tab and click refresh to see them.")
    
    def _update_queue_item(self, workshop_id: str, icon: str, status: str):
        """Update a queue item's display."""
        for i in range(self.queue_list.count()):
            item = self.queue_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == workshop_id:
                item.setText(f"{icon} {workshop_id} - {status}")
                break
    
    def _cancel_downloads(self):
        """Cancel current downloads."""
        if self._worker:
            self._worker.cancel()
            self._log_info("Cancelling downloads...")
    
    def _clear_log(self):
        """Clear the log."""
        self.log_text.clear()
    
    def is_downloading(self) -> bool:
        """Check if downloads are in progress."""
        return self._worker is not None and self._worker.isRunning()


class SteamCMDSetupWidget(QWidget):
    """
    Widget to help users install SteamCMD.
    """
    
    setup_complete = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._process: Optional[QProcess] = None
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Warning
        warning = QLabel(
            "<h2>⚠️ SteamCMD Not Found</h2>"
            "<p>SteamCMD is required to download mods from Steam Workshop.</p>"
        )
        warning.setWordWrap(True)
        layout.addWidget(warning)
        
        # Install command
        cmd = SteamCMDChecker.get_install_command()
        cmd_label = QLabel(f"<p>Install with:</p><pre>{cmd}</pre>")
        cmd_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(cmd_label)
        
        # Manual instructions
        manual = QLabel(
            "<p><b>Manual steps:</b></p>"
            "<ol>"
            "<li>Open a terminal</li>"
            "<li>Run the command above</li>"
            "<li>Wait for installation to complete</li>"
            "<li>Click 'Check Again' below</li>"
            "</ol>"
        )
        manual.setWordWrap(True)
        layout.addWidget(manual)
        
        # Log area for auto-install attempt
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setVisible(False)
        self.log_text.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4;")
        layout.addWidget(self.log_text)
        
        layout.addStretch()
        
        # Buttons
        buttons = QHBoxLayout()
        
        self.btn_check = QPushButton("🔄 Check Again")
        self.btn_check.clicked.connect(self._check_steamcmd)
        buttons.addWidget(self.btn_check)
        
        buttons.addStretch()
        layout.addLayout(buttons)
    
    def _check_steamcmd(self):
        """Check if SteamCMD is now available."""
        if SteamCMDChecker.is_available():
            self.setup_complete.emit()
        else:
            self.log_text.setVisible(True)
            self.log_text.append("SteamCMD not found. Please install it using the command above.")
