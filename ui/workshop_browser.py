"""
Workshop Browser for RimModManager
Scraper-based Workshop browser with mod cards, requirements checking, and category filters.
No WebEngine needed - uses workshop_scraper.py for all data.
"""

import re
import threading
import logging
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QListWidget, QListWidgetItem, QProgressBar,
    QSplitter, QGroupBox, QCheckBox, QTextEdit,
    QApplication, QScrollArea, QFrame, QSizePolicy, QComboBox,
    QMessageBox, QDialog, QDialogButtonBox, QTabWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QUrl, QTimer
from PyQt6.QtGui import QPixmap, QDesktopServices, QIcon, QFont
from game_detector import PLATFORM
from workshop_scraper import (
    WorkshopMod, WorkshopPage, WorkshopCollection,
    fetch_workshop_page, fetch_mod_details,
    fetch_mod_requirements, fetch_collections_page, fetch_collection_details,
    _get_opener, WORKSHOP_CATEGORIES, WORKSHOP_COLLECTION_CATEGORIES
)

log = logging.getLogger("rimmodmanager.workshop_browser")


@dataclass
class WorkshopItem:
    """Represents a Workshop mod item for the download queue."""
    workshop_id: str
    name: str = ""
    author: str = ""
    description: str = ""
    thumbnail_url: str = ""
    is_collection: bool = False
    required_mod_ids: list[str] = field(default_factory=list)


class DownloadQueueItem(QListWidgetItem):
    """List item for download queue with status."""
    
    def __init__(self, item: WorkshopItem):
        super().__init__()
        self.workshop_item = item
        self.update_display()
    
    def update_display(self, status: str = "Pending"):
        icon = "📦" if not self.workshop_item.is_collection else "📁"
        name = self.workshop_item.name or self.workshop_item.workshop_id
        self.setText(f"{icon} {name} - {status}")


class ThumbLoader(QThread):
    """Background thread to load thumbnail images."""
    finished = pyqtSignal(str, QPixmap)
    
    def __init__(self, workshop_id: str, url: str, parent=None):
        super().__init__(parent)
        self.workshop_id = workshop_id
        self.url = url
        self._abort = False
    
    def run(self):
        try:
            import urllib.request
            req = urllib.request.Request(self.url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                if not self._abort:
                    data = resp.read()
                    pixmap = QPixmap()
                    pixmap.loadFromData(data)
                    self.finished.emit(self.workshop_id, pixmap)
        except Exception:
            pass
    
    def abort(self):
        self._abort = True


class ModDetailFetcher(QThread):
    """Background thread to fetch full mod details including requirements."""
    finished = pyqtSignal(object)
    error = pyqtSignal(str, str)
    
    def __init__(self, workshop_id: str, parent=None):
        super().__init__(parent)
        self.workshop_id = workshop_id
    
    def run(self):
        try:
            mod = fetch_mod_details(self.workshop_id)
            if mod:
                self.finished.emit(mod)
            else:
                self.error.emit(self.workshop_id, "Failed to fetch mod details")
        except Exception as e:
            self.error.emit(self.workshop_id, str(e))


class CollectionCard(QFrame):
    """A collection card widget with thumbnail, metadata, and action buttons."""
    
    add_requested = pyqtSignal(str)  # collection_id
    details_requested = pyqtSignal(str)  # collection_id
    
    def __init__(self, collection: WorkshopCollection, downloaded_ids: set[str] = None, parent=None):
        super().__init__(parent)
        self.collection = collection
        self.downloaded_ids = downloaded_ids or set()
        self._setup_ui()
    
    def _setup_ui(self):
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            CollectionCard {
                background-color: #1e1e2e;
                border: 1px solid #45475a;
                border-radius: 10px;
                padding: 10px;
            }
            CollectionCard:hover {
                border-color: #f9e2af;
                background-color: #252537;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(14)
        
        # Thumbnail
        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(180, 100)
        self.thumb_label.setMinimumSize(180, 100)
        self.thumb_label.setMaximumSize(180, 100)
        self.thumb_label.setStyleSheet("""
            background-color: #313244;
            border-radius: 6px;
            color: #6c7086;
            font-size: 28px;
        """)
        self.thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb_label.setText("📁")
        layout.addWidget(self.thumb_label, 0)
        
        # Info section
        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)
        
        # Title row
        title_row = QHBoxLayout()
        title_label = QLabel(self.collection.name or f"Collection {self.collection.collection_id}")
        title_label.setStyleSheet("""
            color: #f9e2af;
            font-size: 15px;
            font-weight: bold;
        """)
        title_label.setWordWrap(True)
        title_row.addWidget(title_label, 1)
        
        # Collection badge
        badge = QLabel("📁")
        badge.setToolTip("Collection")
        badge.setStyleSheet("font-size: 16px;")
        title_row.addWidget(badge)
        
        info_layout.addLayout(title_row)
        
        # Author + date row
        meta_row = QHBoxLayout()
        meta_row.setSpacing(12)
        
        if self.collection.author:
            author_label = QLabel(f"👤 {self.collection.author}")
            author_label.setStyleSheet("color: #a6adc8; font-size: 12px;")
            meta_row.addWidget(author_label)
        
        if self.collection.updated_date:
            date_label = QLabel(f"📅 {self.collection.updated_date}")
            date_label.setStyleSheet("color: #6c7086; font-size: 11px;")
            meta_row.addWidget(date_label)
        
        # Mod count
        if self.collection.mod_count > 0:
            count_label = QLabel(f"📦 {self.collection.mod_count} mods")
            count_label.setStyleSheet("color: #94e2d5; font-size: 11px; font-weight: bold;")
            meta_row.addWidget(count_label)
        
        meta_row.addStretch()
        info_layout.addLayout(meta_row)
        
        # Stats row
        if self.collection.subscriptions or self.collection.favorites:
            stats_row = QHBoxLayout()
            stats_row.setSpacing(12)
            
            if self.collection.subscriptions:
                sub_label = QLabel(f"📥 {self.collection.subscriptions}")
                sub_label.setStyleSheet("color: #89b4fa; font-size: 11px;")
                stats_row.addWidget(sub_label)
            
            if self.collection.favorites:
                fav_label = QLabel(f"⭐ {self.collection.favorites}")
                fav_label.setStyleSheet("color: #f9e2af; font-size: 11px;")
                stats_row.addWidget(fav_label)
            
            stats_row.addStretch()
            info_layout.addLayout(stats_row)
        
        # Description
        if self.collection.description:
            desc_label = QLabel(self.collection.description[:180])
            desc_label.setStyleSheet("color: #6c7086; font-size: 11px;")
            desc_label.setWordWrap(True)
            info_layout.addWidget(desc_label)
        
        # Status badges
        badges_row = QHBoxLayout()
        badges_row.setSpacing(8)
        
        if self.collection.collection_id in self.downloaded_ids:
            badge = QLabel("✅ Downloaded")
            badge.setStyleSheet("color: #a6e3a1; font-size: 11px; font-weight: bold;")
            badges_row.addWidget(badge)
        
        badges_row.addStretch()
        info_layout.addLayout(badges_row)
        
        layout.addLayout(info_layout, 1)
        
        # Action buttons
        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(6)
        
        self.btn_add = QPushButton("➕ Add All")
        self.btn_add.setFixedWidth(90)
        self.btn_add.setStyleSheet("""
            QPushButton {
                background-color: #f9e2af;
                color: #1e1e2e;
                border: none;
                border-radius: 6px;
                padding: 8px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #89b4fa;
            }
            QPushButton:disabled {
                background-color: #313244;
                color: #6c7086;
            }
        """)
        
        if self.collection.collection_id in self.downloaded_ids:
            self.btn_add.setText("✅ Added")
            self.btn_add.setEnabled(False)
        
        self.btn_add.clicked.connect(lambda: self.add_requested.emit(self.collection.collection_id))
        actions_layout.addWidget(self.btn_add)
        
        self.btn_details = QPushButton("📋 Details")
        self.btn_details.setFixedWidth(90)
        self.btn_details.setStyleSheet("""
            QPushButton {
                background-color: #313244;
                color: #a6adc8;
                border: none;
                border-radius: 6px;
                padding: 6px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #45475a;
                color: #cdd6f4;
            }
        """)
        self.btn_details.clicked.connect(lambda: self.details_requested.emit(self.collection.collection_id))
        actions_layout.addWidget(self.btn_details)
        
        self.btn_open = QPushButton("🌐")
        self.btn_open.setFixedWidth(90)
        self.btn_open.setToolTip("Open in browser")
        self.btn_open.setStyleSheet("""
            QPushButton {
                background-color: #313244;
                color: #a6adc8;
                border: none;
                border-radius: 6px;
                padding: 6px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #45475a;
                color: #cdd6f4;
            }
        """)
        self.btn_open.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(self.collection.url)))
        actions_layout.addWidget(self.btn_open)
        
        actions_layout.addStretch()
        layout.addLayout(actions_layout, 0)
    
    def load_thumbnail(self):
        """Load thumbnail image asynchronously."""
        if not self.collection.thumbnail_url:
            return
        
        self._loader = ThumbLoader(self.collection.collection_id, self.collection.thumbnail_url, parent=self)
        self._loader.finished.connect(self._on_thumb_loaded, Qt.ConnectionType.QueuedConnection)
        self._loader.start()
    
    def _on_thumb_loaded(self, workshop_id: str, pixmap: QPixmap):
        if workshop_id == self.collection.collection_id and not pixmap.isNull():
            scaled = pixmap.scaled(
                180, 100,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            self.thumb_label.setPixmap(scaled)
            self.thumb_label.setText("")


class CollectionFetcherThread(QThread):
    """Background thread to fetch workshop collections data."""
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    
    def __init__(self, sort: str, page: int, search_text: str = "", parent=None):
        super().__init__(parent)
        self.sort = sort
        self.page = page
        self.search_text = search_text
    
    def run(self):
        try:
            page = fetch_collections_page(
                sort=self.sort,
                page=self.page,
                search_text=self.search_text,
            )
            self.finished.emit(page)
        except Exception as e:
            self.error.emit(str(e))


class CollectionDetailFetcherThread(QThread):
    """Background thread to fetch collection details."""
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    
    def __init__(self, collection_id: str, parent=None):
        super().__init__(parent)
        self.collection_id = collection_id
    
    def run(self):
        try:
            coll = fetch_collection_details(self.collection_id)
            if coll:
                self.finished.emit(coll)
            else:
                self.error.emit(self.collection_id)
        except Exception as e:
            self.error.emit(str(e))


class ModCard(QFrame):
    """A single mod card widget with thumbnail, metadata, and action buttons."""
    
    add_requested = pyqtSignal(str)  # workshop_id
    details_requested = pyqtSignal(str)  # workshop_id
    
    def __init__(self, mod: WorkshopMod, downloaded_ids: set[str] = None, parent=None):
        super().__init__(parent)
        self.mod = mod
        self.downloaded_ids = downloaded_ids or set()
        self._setup_ui()
    
    def _setup_ui(self):
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            ModCard {
                background-color: #1e1e2e;
                border: 1px solid #45475a;
                border-radius: 10px;
                padding: 10px;
            }
            ModCard:hover {
                border-color: #89b4fa;
                background-color: #252537;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(14)
        
        # Thumbnail
        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(180, 100)
        self.thumb_label.setMinimumSize(180, 100)
        self.thumb_label.setMaximumSize(180, 100)
        self.thumb_label.setStyleSheet("""
            background-color: #313244;
            border-radius: 6px;
            color: #6c7086;
            font-size: 28px;
        """)
        self.thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb_label.setText("📦")
        layout.addWidget(self.thumb_label, 0)
        
        # Info section
        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)
        
        # Title row
        title_row = QHBoxLayout()
        title_label = QLabel(self.mod.name or f"Mod {self.mod.workshop_id}")
        title_label.setStyleSheet("""
            color: #cdd6f4;
            font-size: 15px;
            font-weight: bold;
        """)
        title_label.setWordWrap(True)
        title_row.addWidget(title_label, 1)
        
        # Collection badge
        if self.mod.is_collection:
            badge = QLabel("📁")
            badge.setToolTip("Collection")
            badge.setStyleSheet("font-size: 16px;")
            title_row.addWidget(badge)
        
        info_layout.addLayout(title_row)
        
        # Author + date row
        meta_row = QHBoxLayout()
        meta_row.setSpacing(12)
        
        if self.mod.author:
            author_label = QLabel(f"👤 {self.mod.author}")
            author_label.setStyleSheet("color: #a6adc8; font-size: 12px;")
            meta_row.addWidget(author_label)
        
        if self.mod.updated_date:
            date_label = QLabel(f"📅 {self.mod.updated_date}")
            date_label.setStyleSheet("color: #6c7086; font-size: 11px;")
            meta_row.addWidget(date_label)
        
        if self.mod.file_size:
            size_label = QLabel(f"💾 {self.mod.file_size}")
            size_label.setStyleSheet("color: #6c7086; font-size: 11px;")
            meta_row.addWidget(size_label)
        
        meta_row.addStretch()
        info_layout.addLayout(meta_row)
        
        # Stats row
        if self.mod.subscriptions or self.mod.favorites:
            stats_row = QHBoxLayout()
            stats_row.setSpacing(12)
            
            if self.mod.subscriptions:
                sub_label = QLabel(f"📥 {self.mod.subscriptions}")
                sub_label.setStyleSheet("color: #89b4fa; font-size: 11px;")
                stats_row.addWidget(sub_label)
            
            if self.mod.favorites:
                fav_label = QLabel(f"⭐ {self.mod.favorites}")
                fav_label.setStyleSheet("color: #f9e2af; font-size: 11px;")
                stats_row.addWidget(fav_label)
            
            if self.mod.change_notes > 0:
                changes_label = QLabel(f"📝 {self.mod.change_notes} updates")
                changes_label.setStyleSheet("color: #a6e3a1; font-size: 11px;")
                stats_row.addWidget(changes_label)
            
            stats_row.addStretch()
            info_layout.addLayout(stats_row)
        
        # Tags row
        if self.mod.tags:
            tags_row = QHBoxLayout()
            tags_row.setSpacing(6)
            for tag in self.mod.tags[:5]:
                tag_label = QLabel(tag)
                tag_label.setStyleSheet("""
                    background-color: #313244;
                    color: #94e2d5;
                    padding: 2px 8px;
                    border-radius: 4px;
                    font-size: 10px;
                """)
                tags_row.addWidget(tag_label)
            tags_row.addStretch()
            info_layout.addLayout(tags_row)
        
        # Description
        if self.mod.description:
            desc_label = QLabel(self.mod.description[:180])
            desc_label.setStyleSheet("color: #6c7086; font-size: 11px;")
            desc_label.setWordWrap(True)
            info_layout.addWidget(desc_label)
        
        # Requirements warning
        if self.mod.required_mod_ids and not self.mod.has_all_requirements:
            req_row = QHBoxLayout()
            req_row.setSpacing(6)
            warn_label = QLabel("⚠️ Missing requirements:")
            warn_label.setStyleSheet("color: #f38ba8; font-size: 11px; font-weight: bold;")
            req_row.addWidget(warn_label)
            
            for req_id in self.mod.missing_requirements[:3]:
                req_badge = QLabel(req_id)
                req_badge.setStyleSheet("""
                    background-color: #452727;
                    color: #f38ba8;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-size: 10px;
                    font-family: monospace;
                """)
                req_row.addWidget(req_badge)
            
            if len(self.mod.missing_requirements) > 3:
                more_label = QLabel(f"+{len(self.mod.missing_requirements) - 3} more")
                more_label.setStyleSheet("color: #f38ba8; font-size: 10px;")
                req_row.addWidget(more_label)
            
            req_row.addStretch()
            info_layout.addLayout(req_row)
        
        # Status badges
        badges_row = QHBoxLayout()
        badges_row.setSpacing(8)
        
        if self.mod.workshop_id in self.downloaded_ids:
            badge = QLabel("✅ Downloaded")
            badge.setStyleSheet("color: #a6e3a1; font-size: 11px; font-weight: bold;")
            badges_row.addWidget(badge)
        
        if self.mod.has_all_requirements and self.mod.required_mod_ids:
            badge = QLabel("✅ Requirements met")
            badge.setStyleSheet("color: #a6e3a1; font-size: 11px;")
            badges_row.addWidget(badge)
        
        badges_row.addStretch()
        info_layout.addLayout(badges_row)
        
        layout.addLayout(info_layout, 1)
        
        # Action buttons
        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(6)
        
        self.btn_add = QPushButton("➕ Add")
        self.btn_add.setFixedWidth(90)
        self.btn_add.setStyleSheet("""
            QPushButton {
                background-color: #45475a;
                color: #cdd6f4;
                border: none;
                border-radius: 6px;
                padding: 8px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #89b4fa;
                color: #1e1e2e;
            }
            QPushButton:disabled {
                background-color: #313244;
                color: #6c7086;
            }
        """)
        
        if self.mod.workshop_id in self.downloaded_ids:
            self.btn_add.setText("✅ Added")
            self.btn_add.setEnabled(False)
        
        self.btn_add.clicked.connect(lambda: self.add_requested.emit(self.mod.workshop_id))
        actions_layout.addWidget(self.btn_add)
        
        self.btn_details = QPushButton("📋 Details")
        self.btn_details.setFixedWidth(90)
        self.btn_details.setStyleSheet("""
            QPushButton {
                background-color: #313244;
                color: #a6adc8;
                border: none;
                border-radius: 6px;
                padding: 6px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #45475a;
                color: #cdd6f4;
            }
        """)
        self.btn_details.clicked.connect(lambda: self.details_requested.emit(self.mod.workshop_id))
        actions_layout.addWidget(self.btn_details)
        
        self.btn_open = QPushButton("🌐")
        self.btn_open.setFixedWidth(90)
        self.btn_open.setToolTip("Open in browser")
        self.btn_open.setStyleSheet("""
            QPushButton {
                background-color: #313244;
                color: #a6adc8;
                border: none;
                border-radius: 6px;
                padding: 6px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #45475a;
                color: #cdd6f4;
            }
        """)
        self.btn_open.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(self.mod.url)))
        actions_layout.addWidget(self.btn_open)
        
        actions_layout.addStretch()
        layout.addLayout(actions_layout, 0)
    
    def load_thumbnail(self):
        """Load thumbnail image asynchronously."""
        if not self.mod.thumbnail_url:
            return
        
        self._loader = ThumbLoader(self.mod.workshop_id, self.mod.thumbnail_url, parent=self)
        self._loader.finished.connect(self._on_thumb_loaded, Qt.ConnectionType.QueuedConnection)
        self._loader.start()
    
    def _on_thumb_loaded(self, workshop_id: str, pixmap: QPixmap):
        if workshop_id == self.mod.workshop_id and not pixmap.isNull():
            scaled = pixmap.scaled(
                180, 100,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            self.thumb_label.setPixmap(scaled)
            self.thumb_label.setText("")
    
    def update_requirements(self, mod: WorkshopMod):
        """Update the card with fetched requirement info."""
        self.mod = mod
        # Rebuild the UI with new requirement info
        # For now, just update the missing requirements
        self.mod.has_all_requirements = len(mod.missing_requirements) == 0


class WorkshopFetcherThread(QThread):
    """Background thread to fetch workshop browse data."""
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    
    def __init__(self, sort: str, page: int, search_text: str = "", tag: str = "", parent=None):
        super().__init__(parent)
        self.sort = sort
        self.page = page
        self.search_text = search_text
        self.tag = tag
    
    def run(self):
        try:
            page = fetch_workshop_page(
                sort=self.sort,
                page=self.page,
                search_text=self.search_text,
                tag=self.tag,
            )
            self.finished.emit(page)
        except Exception as e:
            self.error.emit(str(e))


class RequirementsDialog(QDialog):
    """Dialog showing mod requirements and allowing auto-add of missing ones."""
    
    add_all_requested = pyqtSignal(list)  # list of missing mod IDs
    
    def __init__(self, mod: WorkshopMod, missing_ids: list[str], parent=None):
        super().__init__(parent)
        self.mod = mod
        self.missing_ids = missing_ids
        self.setWindowTitle(f"Requirements for {mod.name}")
        self.setMinimumWidth(500)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel(f"📋 Requirements for: {self.mod.name}")
        header.setStyleSheet("color: #cdd6f4; font-size: 16px; font-weight: bold;")
        layout.addWidget(header)
        
        # Requirements list
        list_label = QLabel("Missing requirements:")
        list_label.setStyleSheet("color: #a6adc8; font-size: 13px; margin-top: 10px;")
        layout.addWidget(list_label)
        
        self.req_list = QListWidget()
        self.req_list.setStyleSheet("""
            QListWidget {
                background-color: #1e1e2e;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 6px;
            }
        """)
        
        for req_id in self.missing_ids:
            item = QListWidgetItem(f"📦 Mod ID: {req_id}")
            item.setCheckState(Qt.CheckState.Checked)
            self.req_list.addItem(item)
        
        layout.addWidget(self.req_list)
        
        # Info
        info = QLabel("💡 These mods are required for the selected mod to work properly.")
        info.setStyleSheet("color: #6c7086; font-size: 11px; font-style: italic;")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)
        
        btn_add_selected = QPushButton("Add Selected")
        btn_add_selected.setStyleSheet("""
            QPushButton {
                background-color: #45475a;
                color: #cdd6f4;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #89b4fa;
                color: #1e1e2e;
            }
        """)
        btn_add_selected.clicked.connect(self._add_selected)
        btn_layout.addWidget(btn_add_selected)
        
        btn_add_all = QPushButton("Add All + Main Mod")
        btn_add_all.setStyleSheet("""
            QPushButton {
                background-color: #a6e3a1;
                color: #1e1e2e;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #94e2d5;
            }
        """)
        btn_add_all.clicked.connect(self._add_all)
        btn_layout.addWidget(btn_add_all)
        
        layout.addLayout(btn_layout)
    
    def _add_selected(self):
        ids = []
        for i in range(self.req_list.count()):
            item = self.req_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                # Extract ID from text
                match = re.search(r'(\d+)', item.text())
                if match:
                    ids.append(match.group(1))
        self.add_all_requested.emit(ids)
        self.accept()
    
    def _add_all(self):
        ids = [self.mod.workshop_id]
        for i in range(self.req_list.count()):
            item = self.req_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                match = re.search(r'(\d+)', item.text())
                if match:
                    ids.append(match.group(1))
        self.add_all_requested.emit(ids)
        self.accept()


class WorkshopBrowser(QWidget):
    """
    Integrated Steam Workshop browser widget.
    Uses scraper-based approach with full metadata and requirements checking.
    """
    
    mod_added = pyqtSignal(str, str)  # workshop_id, name
    download_requested = pyqtSignal(list)  # list of workshop_ids
    
    WORKSHOP_URL = "https://steamcommunity.com/app/294100/workshop/"
    
    def __init__(self, downloaded_ids: set[str] = None, parent=None, disable_webengine: bool = False):
        super().__init__(parent)
        self.downloaded_ids = downloaded_ids or set()
        self.queue: list[WorkshopItem] = []
        self.queue_ids: set[str] = set()
        self._queueLock = threading.Lock()
        self._disable_webengine = disable_webengine
        
        # Scraper state - Mods
        self.current_sort = "toprated"
        self.current_tag = ""
        self.current_page = 1
        self.current_search = ""
        self.current_workshop_page: Optional[WorkshopPage] = None
        self.mod_cards: list[ModCard] = []
        self._fetcher_thread: Optional[WorkshopFetcherThread] = None
        self._detail_threads: dict[str, ModDetailFetcher] = {}
        
        # Scraper state - Collections
        self.current_collection_sort = "toprated"
        self.current_collection_page = 1
        self.current_collection_search = ""
        self.current_collection_page_data: Optional[WorkshopPage] = None
        self.collection_cards: list[CollectionCard] = []
        self._collection_fetcher_thread: Optional[CollectionFetcherThread] = None
        self._collection_detail_threads: dict[str, CollectionDetailFetcherThread] = {}
        
        # Cache for mod details
        self._mod_details_cache: dict[str, WorkshopMod] = {}
        self._collection_details_cache: dict[str, WorkshopCollection] = {}
        
        self._collections_tab_shown = False
        
        self._setup_ui()
        
        # Auto-fetch on init (safe with error handling)
        try:
            QTimer.singleShot(300, self._fetch_workshop)
        except Exception:
            pass
    
    def cleanup(self):
        """Clean up all running threads safely."""
        # Stop main fetcher thread
        if self._fetcher_thread and self._fetcher_thread.isRunning():
            self._fetcher_thread.quit()
            self._fetcher_thread.wait(2000)
        
        # Stop collection fetcher thread
        if self._collection_fetcher_thread and self._collection_fetcher_thread.isRunning():
            self._collection_fetcher_thread.quit()
            self._collection_fetcher_thread.wait(2000)
        
        # Stop all detail fetcher threads
        for thread in list(self._detail_threads.values()):
            if thread.isRunning():
                thread.quit()
                thread.wait(2000)
        self._detail_threads.clear()
        
        # Stop all collection detail fetcher threads
        for thread in list(self._collection_detail_threads.values()):
            if thread.isRunning():
                thread.quit()
                thread.wait(2000)
        self._collection_detail_threads.clear()
        
        # Clear caches
        self._mod_details_cache.clear()
        self._collection_details_cache.clear()
    
    def closeEvent(self, event):
        self.cleanup()
        super().closeEvent(event)
    
    def _setup_ui(self):
        """Set up the browser UI with Mods and Collections tabs."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side - Tabbed browser
        browser_widget = QWidget()
        browser_layout = QVBoxLayout(browser_widget)
        browser_layout.setContentsMargins(6, 6, 6, 6)
        
        # Tab widget for Mods and Collections
        self.content_tabs = QTabWidget()
        self.content_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
            }
            QTabBar::tab {
                background-color: #313244;
                color: #a6adc8;
                padding: 8px 16px;
                border: 1px solid #45475a;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #45475a;
                color: #cdd6f4;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background-color: #45475a;
            }
        """)
        
        # Mods tab
        mods_tab = self._create_mods_tab()
        self.content_tabs.addTab(mods_tab, "📦 Mods")
        
        # Collections tab
        collections_tab = self._create_collections_tab()
        self.content_tabs.addTab(collections_tab, "📁 Collections")
        
        browser_layout.addWidget(self.content_tabs, 1)
        
        splitter.addWidget(browser_widget)
        
        # Right side - Queue
        queue_widget = QWidget()
        queue_widget.setMaximumWidth(380)
        queue_widget.setMinimumWidth(280)
        queue_layout = QVBoxLayout(queue_widget)
        queue_layout.setContentsMargins(4, 4, 4, 4)
        
        queue_header = QHBoxLayout()
        queue_header.addWidget(QLabel("📥 Download Queue"))
        queue_header.addStretch()
        self.queue_count = QLabel("(0)")
        self.queue_count.setStyleSheet("color: #89b4fa; font-weight: bold;")
        queue_header.addWidget(self.queue_count)
        queue_layout.addLayout(queue_header)
        
        self.queue_list = QListWidget()
        self.queue_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.queue_list.setStyleSheet("""
            QListWidget {
                background-color: #1e1e2e;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 6px;
            }
        """)
        queue_layout.addWidget(self.queue_list, 1)
        
        # Queue controls
        queue_controls = QHBoxLayout()
        self.btn_select_all = QPushButton("Select All")
        self.btn_select_all.clicked.connect(self._select_all_queue)
        queue_controls.addWidget(self.btn_select_all)
        
        self.btn_remove = QPushButton("🗑️ Remove")
        self.btn_remove.clicked.connect(self._remove_selected)
        queue_controls.addWidget(self.btn_remove)
        
        self.btn_clear = QPushButton("Clear All")
        self.btn_clear.clicked.connect(self._clear_queue)
        queue_controls.addWidget(self.btn_clear)
        queue_layout.addLayout(queue_controls)
        
        # Options
        self.dup_check = QCheckBox("Skip already downloaded mods")
        self.dup_check.setChecked(True)
        self.dup_check.setStyleSheet("color: #a6adc8;")
        queue_layout.addWidget(self.dup_check)
        
        self.auto_req_check = QCheckBox("Auto-add missing requirements")
        self.auto_req_check.setChecked(True)
        self.auto_req_check.setStyleSheet("color: #a6adc8;")
        queue_layout.addWidget(self.auto_req_check)
        
        # Batch input
        batch_group = QGroupBox("Batch Add (IDs/URLs)")
        batch_group.setStyleSheet("""
            QGroupBox {
                color: #a6adc8;
                border: 1px solid #45475a;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        batch_layout = QVBoxLayout(batch_group)
        
        self.batch_input = QTextEdit()
        self.batch_input.setMaximumHeight(80)
        self.batch_input.setPlaceholderText("Paste multiple mod IDs or URLs here (one per line)")
        self.batch_input.setStyleSheet("""
            QTextEdit {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 4px;
                padding: 6px;
            }
        """)
        batch_layout.addWidget(self.batch_input)
        
        batch_btns = QHBoxLayout()
        self.btn_add_batch = QPushButton("Add All")
        self.btn_add_batch.clicked.connect(self._add_batch)
        batch_btns.addWidget(self.btn_add_batch)
        
        batch_layout.addLayout(batch_btns)
        queue_layout.addWidget(batch_group)
        
        # Download button
        self.btn_download = QPushButton("⬇️ Download All")
        self.btn_download.setStyleSheet("""
            QPushButton {
                background-color: #a6e3a1;
                color: #1e1e2e;
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #94e2d5;
            }
            QPushButton:disabled {
                background-color: #45475a;
                color: #6c7086;
            }
        """)
        self.btn_download.clicked.connect(self._start_download)
        queue_layout.addWidget(self.btn_download)
        
        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        queue_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #6c7086; font-size: 11px;")
        self.status_label.setWordWrap(True)
        queue_layout.addWidget(self.status_label)
        
        splitter.addWidget(queue_widget)
        splitter.setSizes([750, 330])
        
        layout.addWidget(splitter, 1)
        
        # Auto-fetch collections when tab is first shown
        self.content_tabs.currentChanged.connect(self._on_tab_changed)
        self._collections_tab_shown = False
    
    def _create_mods_tab(self) -> QWidget:
        """Create the Mods tab content."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Top bar: Search + Category dropdown
        top_bar = QHBoxLayout()
        top_bar.setSpacing(8)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search Workshop mods...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #89b4fa;
            }
        """)
        self.search_input.returnPressed.connect(self._do_search)
        top_bar.addWidget(self.search_input, 1)
        
        self.btn_search = QPushButton("🔍")
        self.btn_search.setFixedWidth(40)
        self.btn_search.setToolTip("Search")
        self.btn_search.clicked.connect(self._do_search)
        top_bar.addWidget(self.btn_search)
        
        self.category_combo = QComboBox()
        self.category_combo.setStyleSheet("""
            QComboBox {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
                min-width: 150px;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: #1e1e2e;
                color: #cdd6f4;
                selection-background-color: #45475a;
            }
        """)
        
        for label, sort, tag in WORKSHOP_CATEGORIES:
            if label == "---":
                self.category_combo.insertSeparator(self.category_combo.count())
            else:
                self.category_combo.addItem(label, (sort, tag))
        
        self.category_combo.currentIndexChanged.connect(self._on_category_changed)
        top_bar.addWidget(self.category_combo)
        
        layout.addLayout(top_bar)
        
        # Navigation bar
        nav_bar = QHBoxLayout()
        nav_bar.setSpacing(6)
        
        self.btn_back = QPushButton("←")
        self.btn_back.setFixedWidth(36)
        self.btn_back.setToolTip("Previous page")
        self.btn_back.clicked.connect(self._prev_page)
        self.btn_back.setStyleSheet(self._nav_btn_style())
        nav_bar.addWidget(self.btn_back)
        
        self.btn_forward = QPushButton("→")
        self.btn_forward.setFixedWidth(36)
        self.btn_forward.setToolTip("Next page")
        self.btn_forward.clicked.connect(self._next_page)
        self.btn_forward.setStyleSheet(self._nav_btn_style())
        nav_bar.addWidget(self.btn_forward)
        
        self.btn_refresh = QPushButton("🔄")
        self.btn_refresh.setFixedWidth(36)
        self.btn_refresh.setToolTip("Refresh")
        self.btn_refresh.clicked.connect(lambda: self._fetch_workshop())
        self.btn_refresh.setStyleSheet(self._nav_btn_style())
        nav_bar.addWidget(self.btn_refresh)
        
        self.btn_home = QPushButton("🏠")
        self.btn_home.setFixedWidth(36)
        self.btn_home.setToolTip("Open Workshop in browser")
        self.btn_home.clicked.connect(lambda: self._open_in_browser(self.WORKSHOP_URL))
        self.btn_home.setStyleSheet(self._nav_btn_style())
        nav_bar.addWidget(self.btn_home)
        
        self.page_info_label = QLabel("Loading...")
        self.page_info_label.setStyleSheet("color: #a6adc8; font-size: 12px; padding-left: 8px;")
        nav_bar.addWidget(self.page_info_label, 1)
        
        nav_bar.addStretch()
        layout.addLayout(nav_bar)
        
        # Scrollable mod cards area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #181825;
                border-radius: 8px;
            }
            QScrollBar:vertical {
                background-color: #1e1e2e;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #45475a;
                border-radius: 5px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #585b70;
            }
        """)
        
        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(8, 8, 8, 8)
        self.cards_layout.setSpacing(10)
        self.cards_layout.addStretch()
        
        self.scroll_area.setWidget(self.cards_container)
        layout.addWidget(self.scroll_area, 1)
        
        # Loading indicator
        self.loading_label = QLabel("⏳ Loading workshop data...")
        self.loading_label.setStyleSheet("color: #89b4fa; font-size: 14px; padding: 40px;")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.loading_label)
        
        return tab
    
    def _create_collections_tab(self) -> QWidget:
        """Create the Collections tab content."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Top bar: Search + Category dropdown
        top_bar = QHBoxLayout()
        top_bar.setSpacing(8)
        
        self.collection_search_input = QLineEdit()
        self.collection_search_input.setPlaceholderText("🔍 Search Workshop collections...")
        self.collection_search_input.setStyleSheet("""
            QLineEdit {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #f9e2af;
            }
        """)
        self.collection_search_input.returnPressed.connect(self._do_collection_search)
        top_bar.addWidget(self.collection_search_input, 1)
        
        self.btn_collection_search = QPushButton("🔍")
        self.btn_collection_search.setFixedWidth(40)
        self.btn_collection_search.setToolTip("Search")
        self.btn_collection_search.clicked.connect(self._do_collection_search)
        top_bar.addWidget(self.btn_collection_search)
        
        self.collection_category_combo = QComboBox()
        self.collection_category_combo.setStyleSheet("""
            QComboBox {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
                min-width: 150px;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: #1e1e2e;
                color: #cdd6f4;
                selection-background-color: #45475a;
            }
        """)
        
        for label, sort in WORKSHOP_COLLECTION_CATEGORIES:
            self.collection_category_combo.addItem(label, sort)
        
        self.collection_category_combo.currentIndexChanged.connect(self._on_collection_category_changed)
        top_bar.addWidget(self.collection_category_combo)
        
        layout.addLayout(top_bar)
        
        # Navigation bar
        nav_bar = QHBoxLayout()
        nav_bar.setSpacing(6)
        
        self.btn_collection_back = QPushButton("←")
        self.btn_collection_back.setFixedWidth(36)
        self.btn_collection_back.setToolTip("Previous page")
        self.btn_collection_back.clicked.connect(self._prev_collection_page)
        self.btn_collection_back.setStyleSheet(self._nav_btn_style())
        nav_bar.addWidget(self.btn_collection_back)
        
        self.btn_collection_forward = QPushButton("→")
        self.btn_collection_forward.setFixedWidth(36)
        self.btn_collection_forward.setToolTip("Next page")
        self.btn_collection_forward.clicked.connect(self._next_collection_page)
        self.btn_collection_forward.setStyleSheet(self._nav_btn_style())
        nav_bar.addWidget(self.btn_collection_forward)
        
        self.btn_collection_refresh = QPushButton("🔄")
        self.btn_collection_refresh.setFixedWidth(36)
        self.btn_collection_refresh.setToolTip("Refresh")
        self.btn_collection_refresh.clicked.connect(lambda: self._fetch_collections())
        self.btn_collection_refresh.setStyleSheet(self._nav_btn_style())
        nav_bar.addWidget(self.btn_collection_refresh)
        
        self.btn_collection_home = QPushButton("🏠")
        self.btn_collection_home.setFixedWidth(36)
        self.btn_collection_home.setToolTip("Open Collections in browser")
        self.btn_collection_home.clicked.connect(lambda: self._open_in_browser("https://steamcommunity.com/workshop/browse/?appid=294100&section=collections"))
        self.btn_collection_home.setStyleSheet(self._nav_btn_style())
        nav_bar.addWidget(self.btn_collection_home)
        
        self.collection_page_info_label = QLabel("Loading...")
        self.collection_page_info_label.setStyleSheet("color: #a6adc8; font-size: 12px; padding-left: 8px;")
        nav_bar.addWidget(self.collection_page_info_label, 1)
        
        nav_bar.addStretch()
        layout.addLayout(nav_bar)
        
        # Scrollable collection cards area
        self.collection_scroll_area = QScrollArea()
        self.collection_scroll_area.setWidgetResizable(True)
        self.collection_scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #181825;
                border-radius: 8px;
            }
            QScrollBar:vertical {
                background-color: #1e1e2e;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #45475a;
                border-radius: 5px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #585b70;
            }
        """)
        
        self.collection_cards_container = QWidget()
        self.collection_cards_layout = QVBoxLayout(self.collection_cards_container)
        self.collection_cards_layout.setContentsMargins(8, 8, 8, 8)
        self.collection_cards_layout.setSpacing(10)
        self.collection_cards_layout.addStretch()
        
        self.collection_scroll_area.setWidget(self.collection_cards_container)
        layout.addWidget(self.collection_scroll_area, 1)
        
        # Loading indicator
        self.collection_loading_label = QLabel("⏳ Loading collections...")
        self.collection_loading_label.setStyleSheet("color: #f9e2af; font-size: 14px; padding: 40px;")
        self.collection_loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.collection_loading_label)
        
        return tab
    
    def _nav_btn_style(self) -> str:
        return """
            QPushButton {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45475a;
            }
            QPushButton:disabled {
                background-color: #1e1e2e;
                color: #45475a;
            }
        """
    
    def _on_category_changed(self, index: int):
        """Handle category selection change."""
        data = self.category_combo.itemData(index)
        if data:
            sort, tag = data
            if sort:
                self.current_sort = sort
            self.current_tag = tag
            self.current_page = 1
            self._fetch_workshop()
    
    def _set_sort(self, sort: str):
        """Change sort order and reload."""
        self.current_sort = sort
        self.current_tag = ""
        self.current_page = 1
        # Update combo box to match
        for i in range(self.category_combo.count()):
            data = self.category_combo.itemData(i)
            if data and data[0] == sort and data[1] == "":
                self.category_combo.setCurrentIndex(i)
                break
        self._fetch_workshop()
    
    def _do_search(self):
        """Execute search."""
        self.current_search = self.search_input.text().strip()
        self.current_page = 1
        self._fetch_workshop()
    
    def _prev_page(self):
        """Go to previous page."""
        if self.current_page > 1:
            self.current_page -= 1
            self._fetch_workshop()
    
    def _next_page(self):
        """Go to next page."""
        if self.current_workshop_page and self.current_workshop_page.has_next:
            self.current_page += 1
            self._fetch_workshop()
    
    def _fetch_workshop(self):
        """Fetch workshop data in background thread."""
        if self._fetcher_thread and self._fetcher_thread.isRunning():
            return
        
        self.loading_label.show()
        self.loading_label.setText("⏳ Loading workshop data...")
        self.btn_refresh.setEnabled(False)
        
        self._fetcher_thread = WorkshopFetcherThread(
            sort=self.current_sort,
            page=self.current_page,
            search_text=self.current_search,
            tag=self.current_tag,
            parent=self,
        )
        self._fetcher_thread.finished.connect(self._on_fetch_finished, Qt.ConnectionType.QueuedConnection)
        self._fetcher_thread.error.connect(self._on_fetch_error, Qt.ConnectionType.QueuedConnection)
        self._fetcher_thread.start()
    
    def _on_fetch_finished(self, page: WorkshopPage):
        """Handle fetched workshop data."""
        self.loading_label.hide()
        self.btn_refresh.setEnabled(True)
        self.current_workshop_page = page
        
        # Clear existing cards
        for card in self.mod_cards:
            card.setParent(None)
            card.deleteLater()
        self.mod_cards.clear()
        
        # Update page info
        if page.total_results > 0:
            self.page_info_label.setText(
                f"📊 {page.showing_range} | Page {page.current_page} of {page.total_pages}"
            )
        else:
            self.page_info_label.setText("No results found")
        
        # Update nav buttons
        self.btn_back.setEnabled(page.has_prev)
        self.btn_forward.setEnabled(page.has_next)
        
        # Create mod cards
        for mod in page.mods:
            # Check if already downloaded
            if mod.workshop_id in self.downloaded_ids:
                mod.is_downloaded = True
            
            card = ModCard(mod, self.downloaded_ids)
            card.add_requested.connect(self._on_add_requested)
            card.details_requested.connect(self._on_details_requested)
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)
            self.mod_cards.append(card)
            card.load_thumbnail()
            
            # Fetch full details asynchronously for requirements checking
            self._fetch_mod_details_async(mod.workshop_id, card)
        
        QApplication.processEvents()
    
    def _fetch_mod_details_async(self, workshop_id: str, card: ModCard):
        """Fetch full mod details in background for requirements checking."""
        if workshop_id in self._mod_details_cache:
            cached = self._mod_details_cache[workshop_id]
            card.mod = cached
            card.update_requirements(cached)
            return
        
        if workshop_id in self._detail_threads:
            return
        
        fetcher = ModDetailFetcher(workshop_id, parent=self)
        fetcher.finished.connect(lambda m: self._on_mod_details_fetched(m, card), Qt.ConnectionType.QueuedConnection)
        fetcher.error.connect(lambda wid, err: self._on_mod_details_error(wid, err, card), Qt.ConnectionType.QueuedConnection)
        self._detail_threads[workshop_id] = fetcher
        fetcher.start()
    
    def _on_mod_details_fetched(self, mod: WorkshopMod, card: ModCard):
        """Handle fetched mod details."""
        self._mod_details_cache[mod.workshop_id] = mod
        
        # Check requirements
        if mod.required_mod_ids:
            missing = []
            for req_id in mod.required_mod_ids:
                if req_id not in self.downloaded_ids:
                    missing.append(req_id)
            mod.missing_requirements = missing
            mod.has_all_requirements = len(missing) == 0
        
        # Update card
        card.mod = mod
        card.update_requirements(mod)
        
        # Clean up thread
        wid = mod.workshop_id
        if wid in self._detail_threads:
            del self._detail_threads[wid]
    
    def _on_mod_details_error(self, workshop_id: str, error: str, card: ModCard):
        """Handle mod details fetch error."""
        if workshop_id in self._detail_threads:
            del self._detail_threads[workshop_id]
    
    def _on_fetch_error(self, error: str):
        """Handle fetch error."""
        self.loading_label.setText(f"❌ Error: {error}")
        self.loading_label.setStyleSheet("color: #f38ba8; font-size: 13px; padding: 20px;")
        self.btn_refresh.setEnabled(True)
    
    # Collection methods
    def _fetch_collections(self):
        """Fetch collections data in background thread."""
        if self._collection_fetcher_thread and self._collection_fetcher_thread.isRunning():
            return
        
        self.collection_loading_label.show()
        self.collection_loading_label.setText("⏳ Loading collections...")
        self.btn_collection_refresh.setEnabled(False)
        
        self._collection_fetcher_thread = CollectionFetcherThread(
            sort=self.current_collection_sort,
            page=self.current_collection_page,
            search_text=self.current_collection_search,
            parent=self,
        )
        self._collection_fetcher_thread.finished.connect(self._on_collection_fetch_finished, Qt.ConnectionType.QueuedConnection)
        self._collection_fetcher_thread.error.connect(self._on_collection_fetch_error, Qt.ConnectionType.QueuedConnection)
        self._collection_fetcher_thread.start()
    
    def _on_collection_fetch_finished(self, page: WorkshopPage):
        """Handle fetched collections data."""
        self.collection_loading_label.hide()
        self.btn_collection_refresh.setEnabled(True)
        self.current_collection_page_data = page
        
        # Clear existing cards
        for card in self.collection_cards:
            card.setParent(None)
            card.deleteLater()
        self.collection_cards.clear()
        
        # Update page info
        if page.total_results > 0:
            self.collection_page_info_label.setText(
                f"📊 {page.showing_range} | Page {page.current_page} of {page.total_pages}"
            )
        else:
            self.collection_page_info_label.setText("No collections found")
        
        # Update nav buttons
        self.btn_collection_back.setEnabled(page.has_prev)
        self.btn_collection_forward.setEnabled(page.has_next)
        
        # Create collection cards
        for coll in page.collections:
            if coll.collection_id in self.downloaded_ids:
                coll.is_downloaded = True
            
            card = CollectionCard(coll, self.downloaded_ids)
            card.add_requested.connect(self._on_collection_add_requested)
            card.details_requested.connect(self._on_collection_details_requested)
            self.collection_cards_layout.insertWidget(self.collection_cards_layout.count() - 1, card)
            self.collection_cards.append(card)
            card.load_thumbnail()
        
        QApplication.processEvents()
    
    def _on_collection_fetch_error(self, error: str):
        """Handle collection fetch error."""
        self.collection_loading_label.setText(f"❌ Error: {error}")
        self.collection_loading_label.setStyleSheet("color: #f38ba8; font-size: 13px; padding: 20px;")
        self.btn_collection_refresh.setEnabled(True)
    
    def _on_collection_category_changed(self, index: int):
        """Handle collection category selection change."""
        sort = self.collection_category_combo.itemData(index)
        if sort:
            self.current_collection_sort = sort
            self.current_collection_page = 1
            self._fetch_collections()
    
    def _do_collection_search(self):
        """Execute collection search."""
        self.current_collection_search = self.collection_search_input.text().strip()
        self.current_collection_page = 1
        self._fetch_collections()
    
    def _prev_collection_page(self):
        """Go to previous collection page."""
        if self.current_collection_page > 1:
            self.current_collection_page -= 1
            self._fetch_collections()
    
    def _next_collection_page(self):
        """Go to next collection page."""
        if self.current_collection_page_data and self.current_collection_page_data.has_next:
            self.current_collection_page += 1
            self._fetch_collections()
    
    def _on_tab_changed(self, index: int):
        """Handle tab change - auto-fetch collections when first shown."""
        if index == 1 and not self._collections_tab_shown:  # Collections tab
            self._collections_tab_shown = True
            QTimer.singleShot(300, self._fetch_collections)
    
    def _on_collection_add_requested(self, collection_id: str):
        """Handle add collection to queue request."""
        self.status_label.setText(f"Fetching collection details...")
        
        fetcher = CollectionDetailFetcherThread(collection_id, parent=self)
        fetcher.finished.connect(lambda c: self._add_collection_to_queue(c), Qt.ConnectionType.QueuedConnection)
        fetcher.error.connect(lambda cid: self.status_label.setText(f"Error fetching collection {cid}"), Qt.ConnectionType.QueuedConnection)
        fetcher.start()
    
    def _add_collection_to_queue(self, collection: WorkshopCollection):
        """Add all mods in a collection to the queue."""
        self._collection_details_cache[collection.collection_id] = collection
        
        added_count = 0
        for mod_id in collection.mod_ids:
            if mod_id not in self.downloaded_ids and mod_id not in self.queue_ids:
                self._add_id_to_queue(mod_id, f"[{collection.name}]")
                added_count += 1
        
        self.status_label.setText(f"Added {added_count} mods from collection: {collection.name}")
    
    def _on_collection_details_requested(self, collection_id: str):
        """Show collection details dialog."""
        if collection_id in self._collection_details_cache:
            coll = self._collection_details_cache[collection_id]
            self._show_collection_details_dialog(coll)
        else:
            self.status_label.setText("Fetching collection details...")
            fetcher = CollectionDetailFetcherThread(collection_id, parent=self)
            fetcher.finished.connect(lambda c: self._show_collection_details_dialog(c), Qt.ConnectionType.QueuedConnection)
            fetcher.error.connect(lambda cid: self.status_label.setText(f"Error: {cid}"), Qt.ConnectionType.QueuedConnection)
            fetcher.start()
    
    def _show_collection_details_dialog(self, collection: WorkshopCollection):
        """Show a dialog with collection details."""
        dialog = QDialog(self)
        dialog.setWindowTitle(collection.name)
        dialog.setMinimumWidth(600)
        dialog.setMinimumHeight(500)
        
        layout = QVBoxLayout(dialog)
        
        # Title
        title = QLabel(f"📁 {collection.name}")
        title.setStyleSheet("color: #f9e2af; font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        # Meta info
        meta = QLabel(f"👤 {collection.author} | 📦 {collection.mod_count} mods")
        meta.setStyleSheet("color: #a6adc8; font-size: 12px;")
        layout.addWidget(meta)
        
        # Stats
        stats = QLabel(f"📥 {collection.subscriptions} | ⭐ {collection.favorites}")
        stats.setStyleSheet("color: #89b4fa; font-size: 12px;")
        layout.addWidget(stats)
        
        # Description
        if collection.description:
            desc = QLabel(collection.description)
            desc.setStyleSheet("color: #cdd6f4; font-size: 12px;")
            desc.setWordWrap(True)
            layout.addWidget(desc)
        
        # Mods list
        mods_label = QLabel(f"Mods in collection ({len(collection.mod_ids)}):")
        mods_label.setStyleSheet("color: #a6adc8; font-size: 13px; margin-top: 10px;")
        layout.addWidget(mods_label)
        
        mods_list = QListWidget()
        mods_list.setStyleSheet("""
            QListWidget {
                background-color: #1e1e2e;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 6px;
            }
        """)
        
        for mod_id in collection.mod_ids[:50]:  # Show first 50
            status = "✅" if mod_id in self.downloaded_ids else "📦"
            item = QListWidgetItem(f"{status} {mod_id}")
            mods_list.addItem(item)
        
        if len(collection.mod_ids) > 50:
            more_item = QListWidgetItem(f"... and {len(collection.mod_ids) - 50} more mods")
            more_item.setStyleSheet("color: #6c7086;")
            mods_list.addItem(more_item)
        
        layout.addWidget(mods_list)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        open_btn = QPushButton("🌐 Open in Browser")
        open_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(collection.url)))
        btn_layout.addWidget(open_btn)
        
        add_all_btn = QPushButton("➕ Add All to Queue")
        add_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #f9e2af;
                color: #1e1e2e;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #89b4fa;
            }
        """)
        add_all_btn.clicked.connect(lambda: self._add_collection_to_queue(collection))
        btn_layout.addWidget(add_all_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        
        dialog.exec()
    
    def _on_add_requested(self, workshop_id: str):
        """Handle add to queue request with requirements checking."""
        # Check if we have cached details
        if workshop_id in self._mod_details_cache:
            mod = self._mod_details_cache[workshop_id]
            if mod.required_mod_ids:
                missing = []
                for req_id in mod.required_mod_ids:
                    if req_id not in self.downloaded_ids and req_id not in self.queue_ids:
                        missing.append(req_id)
                
                if missing:
                    # Show requirements dialog
                    if self.auto_req_check.isChecked():
                        # Auto-add missing requirements
                        self._add_id_to_queue(workshop_id, mod.name)
                        for req_id in missing:
                            self._add_id_to_queue(req_id, f"Required by {mod.name}")
                        self.status_label.setText(f"Added {mod.name} + {len(missing)} requirements")
                        return
                    else:
                        dialog = RequirementsDialog(mod, missing, self)
                        dialog.add_all_requested.connect(self._add_ids_to_queue)
                        dialog.exec()
                        return
        
        # No requirements or already checked
        self._add_id_to_queue(workshop_id)
    
    def _on_details_requested(self, workshop_id: str):
        """Show mod details dialog."""
        if workshop_id in self._mod_details_cache:
            mod = self._mod_details_cache[workshop_id]
            self._show_mod_details_dialog(mod)
        else:
            # Fetch details first
            self.status_label.setText("Fetching mod details...")
            fetcher = ModDetailFetcher(workshop_id, parent=self)
            fetcher.finished.connect(lambda m: self._show_mod_details_dialog(m), Qt.ConnectionType.QueuedConnection)
            fetcher.error.connect(lambda wid, err: self.status_label.setText(f"Error: {err}"), Qt.ConnectionType.QueuedConnection)
            fetcher.start()
    
    def _show_mod_details_dialog(self, mod: WorkshopMod):
        """Show a dialog with full mod details."""
        dialog = QDialog(self)
        dialog.setWindowTitle(mod.name)
        dialog.setMinimumWidth(600)
        dialog.setMinimumHeight(400)
        
        layout = QVBoxLayout(dialog)
        
        # Title
        title = QLabel(f"📦 {mod.name}")
        title.setStyleSheet("color: #cdd6f4; font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        # Meta info
        meta = QLabel(f"👤 {mod.author} | 📅 {mod.updated_date} | 💾 {mod.file_size}")
        meta.setStyleSheet("color: #a6adc8; font-size: 12px;")
        layout.addWidget(meta)
        
        # Stats
        stats = QLabel(f"📥 {mod.subscriptions} | ⭐ {mod.favorites} | 📝 {mod.change_notes} updates")
        stats.setStyleSheet("color: #89b4fa; font-size: 12px;")
        layout.addWidget(stats)
        
        # Tags
        if mod.tags:
            tags_label = QLabel("Tags: " + ", ".join(mod.tags))
            tags_label.setStyleSheet("color: #94e2d5; font-size: 11px;")
            tags_label.setWordWrap(True)
            layout.addWidget(tags_label)
        
        # Requirements
        if mod.required_mod_ids:
            req_label = QLabel("Requirements: " + ", ".join(mod.required_mod_ids))
            req_label.setStyleSheet("color: #f9e2af; font-size: 11px;")
            layout.addWidget(req_label)
        
        # Description
        desc = QLabel(mod.description)
        desc.setStyleSheet("color: #cdd6f4; font-size: 12px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        open_btn = QPushButton("🌐 Open in Browser")
        open_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(mod.url)))
        btn_layout.addWidget(open_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        
        dialog.exec()
    
    def _add_mod_to_queue(self, mod: WorkshopMod):
        """Add a mod to the download queue."""
        with self._queue_lock:
            if mod.workshop_id in self.queue_ids:
                return
            
            item = WorkshopItem(
                workshop_id=mod.workshop_id,
                name=mod.name,
                author=mod.author,
                description=mod.description,
                thumbnail_url=mod.thumbnail_url,
                is_collection=mod.is_collection,
                required_mod_ids=mod.required_mod_ids,
            )
            self.queue.append(item)
            self.queue_ids.add(mod.workshop_id)
            
            queue_item = DownloadQueueItem(item)
            self.queue_list.addItem(queue_item)
            self.queue_count.setText(f"({len(self.queue)})")
            
            self.mod_added.emit(mod.workshop_id, mod.name)
    
    def _add_id_to_queue(self, workshop_id: str, name: str = ""):
        """Add a workshop ID to queue."""
        with self._queue_lock:
            if workshop_id in self.queue_ids:
                return
            
            item = WorkshopItem(workshop_id=workshop_id, name=name)
            self.queue.append(item)
            self.queue_ids.add(workshop_id)
            
            queue_item = DownloadQueueItem(item)
            self.queue_list.addItem(queue_item)
            self.queue_count.setText(f"({len(self.queue)})")
    
    def _add_ids_to_queue(self, ids: list[str]):
        """Add multiple IDs to queue."""
        for wid in ids:
            self._add_id_to_queue(wid)
        self.status_label.setText(f"Added {len(ids)} mods to queue")
    
    def _open_in_browser(self, url: str):
        """Open URL in system browser."""
        QDesktopServices.openUrl(QUrl(url))
    
    def _open_url(self, url: str):
        """Open URL - for compatibility."""
        match = re.search(r'id=(\d+)', url)
        if match:
            self._add_id_to_queue(match.group(1))
        else:
            self._open_in_browser(url)
    
    def _add_current_to_queue(self):
        """Add current URL/ID to queue."""
        text = self.search_input.text().strip() if hasattr(self, 'search_input') else ""
        if not text:
            return
        
        match = re.search(r'id=(\d+)', text)
        if match:
            self._add_id_to_queue(match.group(1))
        elif text.isdigit():
            self._add_id_to_queue(text)
    
    def _on_url_changed(self, url):
        pass
    
    def _navigate_to_url(self):
        self._add_current_to_queue()
    
    # Queue management
    def _select_all_queue(self):
        self.queue_list.selectAll()
    
    def _remove_selected(self):
        for item in self.queue_list.selectedItems():
            if hasattr(item, 'workshop_item'):
                wid = item.workshop_item.workshop_id
                with self._queue_lock:
                    self.queue_ids.discard(wid)
                    self.queue = [q for q in self.queue if q.workshop_id != wid]
            row = self.queue_list.row(item)
            self.queue_list.takeItem(row)
        self.queue_count.setText(f"({self.queue_list.count()})")
    
    def _clear_queue(self):
        self.queue_list.clear()
        with self._queue_lock:
            self.queue.clear()
            self.queue_ids.clear()
        self.queue_count.setText("(0)")
    
    def _add_batch(self):
        """Add multiple IDs/URLs from batch input."""
        text = self.batch_input.toPlainText().strip()
        if not text:
            return
        
        ids = set()
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            # Check for collection URLs
            if 'workshop/collection' in line or 'section=collections' in line:
                match = re.search(r'id=(\d+)', line)
                if match:
                    # Add collection
                    self._on_collection_add_requested(match.group(1))
                    continue
            # Regular mod IDs/URLs
            match = re.search(r'id=(\d+)', line)
            if match:
                ids.add(match.group(1))
            elif line.isdigit():
                ids.add(line)
        
        added = 0
        for wid in ids:
            if wid not in self.queue_ids:
                self._add_id_to_queue(wid)
                added += 1
        
        self.status_label.setText(f"Added {added} mods to queue")
        self.batch_input.clear()
    
    def _parse_collection(self):
        """Parse a collection URL."""
        text = self.batch_input.toPlainText().strip()
        match = re.search(r'id=(\d+)', text)
        if match:
            self._add_id_to_queue(match.group(1))
            self.status_label.setText("Collection added to queue")
    
    def _start_download(self):
        """Start downloading all queued mods."""
        with self._queue_lock:
            ids = [item.workshop_id for item in self.queue]
        
        if not ids:
            self.status_label.setText("Queue is empty!")
            return
        
        self.download_requested.emit(ids)
