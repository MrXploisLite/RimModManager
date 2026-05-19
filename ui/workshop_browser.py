"""
Workshop Browser for RimModManager
Scraper-based Workshop browser with mod cards - no WebEngine needed.
Uses workshop_scraper.py to fetch and parse Steam Workshop data.
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
    QApplication, QScrollArea, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QUrl
from PyQt6.QtGui import QPixmap, QDesktopServices
from game_detector import PLATFORM
from workshop_scraper import (
    WorkshopMod, WorkshopPage, fetch_workshop_page, _get_opener
)

log = logging.getLogger("rimmodmanager.workshop_browser")


@dataclass
class WorkshopItem:
    """Represents a Workshop mod item (alias for WorkshopMod for compatibility)."""
    workshop_id: str
    name: str = ""
    author: str = ""
    description: str = ""
    thumbnail_url: str = ""
    subscribed: bool = False
    downloaded: bool = False
    is_collection: bool = False
    collection_items: list[str] = field(default_factory=list)


class DownloadQueueItem(QListWidgetItem):
    """List item for download queue."""
    
    def __init__(self, item: WorkshopItem):
        super().__init__()
        self.workshop_item = item
        self.update_display()
    
    def update_display(self, status: str = "Pending"):
        icon = "📦" if not self.workshop_item.is_collection else "📁"
        name = self.workshop_item.name or self.workshop_item.workshop_id
        self.setText(f"{icon} {name} - {status}")


class ModCard(QFrame):
    """A single mod card widget with thumbnail, info, and add button."""
    
    add_requested = pyqtSignal(str)  # workshop_id
    
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
                border-radius: 8px;
                padding: 8px;
            }
            ModCard:hover {
                border-color: #89b4fa;
                background-color: #252537;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)
        
        # Thumbnail
        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(160, 90)
        self.thumb_label.setStyleSheet("""
            background-color: #313244;
            border-radius: 4px;
        """)
        self.thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb_label.setText("📦")
        self.thumb_label.setStyleSheet("""
            background-color: #313244;
            border-radius: 4px;
            color: #6c7086;
            font-size: 24px;
        """)
        layout.addWidget(self.thumb_label, 0)
        
        # Info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        # Title
        title_label = QLabel(self.mod.name or f"Mod {self.mod.workshop_id}")
        title_label.setStyleSheet("""
            color: #cdd6f4;
            font-size: 14px;
            font-weight: bold;
        """)
        title_label.setWordWrap(True)
        info_layout.addWidget(title_label)
        
        # Author
        if self.mod.author:
            author_label = QLabel(f"by {self.mod.author}")
            author_label.setStyleSheet("color: #a6adc8; font-size: 12px;")
            info_layout.addWidget(author_label)
        
        # Description
        if self.mod.description:
            desc_label = QLabel(self.mod.description[:150])
            desc_label.setStyleSheet("color: #6c7086; font-size: 11px;")
            desc_label.setWordWrap(True)
            info_layout.addWidget(desc_label)
        
        # Status badges
        badges_layout = QHBoxLayout()
        badges_layout.setSpacing(8)
        
        if self.mod.workshop_id in self.downloaded_ids:
            badge = QLabel("✅ Downloaded")
            badge.setStyleSheet("color: #a6e3a1; font-size: 11px; font-weight: bold;")
            badges_layout.addWidget(badge)
        
        if self.mod.is_collection:
            badge = QLabel("📁 Collection")
            badge.setStyleSheet("color: #f9e2af; font-size: 11px;")
            badges_layout.addWidget(badge)
        
        badges_layout.addStretch()
        info_layout.addLayout(badges_layout)
        
        layout.addLayout(info_layout, 1)
        
        # Add button
        self.btn_add = QPushButton("➕ Add")
        self.btn_add.setFixedWidth(80)
        self.btn_add.setStyleSheet("""
            QPushButton {
                background-color: #45475a;
                color: #cdd6f4;
                border: none;
                border-radius: 4px;
                padding: 6px;
                font-size: 12px;
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
        layout.addWidget(self.btn_add, 0)
    
    def load_thumbnail(self):
        """Load thumbnail image asynchronously."""
        if not self.mod.thumbnail_url:
            return
        
        class ThumbLoader(QThread):
            finished = pyqtSignal(QPixmap)
            
            def __init__(self, url):
                super().__init__()
                self.url = url
            
            def run(self):
                try:
                    import urllib.request
                    req = urllib.request.Request(self.url, headers={
                        "User-Agent": "Mozilla/5.0"
                    })
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        data = resp.read()
                        pixmap = QPixmap()
                        pixmap.loadFromData(data)
                        self.finished.emit(pixmap)
                except Exception:
                    pass
        
        self._loader = ThumbLoader(self.mod.thumbnail_url)
        self._loader.finished.connect(self._on_thumb_loaded)
        self._loader.start()
    
    def _on_thumb_loaded(self, pixmap: QPixmap):
        if not pixmap.isNull():
            scaled = pixmap.scaled(
                160, 90,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            self.thumb_label.setPixmap(scaled)
            self.thumb_label.setText("")


class WorkshopFetcherThread(QThread):
    """Background thread to fetch workshop data."""
    finished = pyqtSignal(object)  # WorkshopPage
    error = pyqtSignal(str)
    
    def __init__(self, sort: str, page: int, search_text: str = ""):
        super().__init__()
        self.sort = sort
        self.page = page
        self.search_text = search_text
    
    def run(self):
        try:
            page = fetch_workshop_page(
                sort=self.sort,
                page=self.page,
                search_text=self.search_text,
            )
            self.finished.emit(page)
        except Exception as e:
            self.error.emit(str(e))


class WorkshopBrowser(QWidget):
    """
    Integrated Steam Workshop browser widget.
    Uses scraper-based approach (no WebEngine needed).
    """
    
    # Signals
    mod_added = pyqtSignal(str, str)  # workshop_id, name
    download_requested = pyqtSignal(list)  # list of workshop_ids
    
    WORKSHOP_URL = "https://steamcommunity.com/app/294100/workshop/"
    WORKSHOP_BROWSE_URL = "https://steamcommunity.com/workshop/browse/?appid=294100"
    
    def __init__(self, downloaded_ids: set[str] = None, parent=None, disable_webengine: bool = False):
        super().__init__(parent)
        self.downloaded_ids = downloaded_ids or set()
        self.queue: list[WorkshopItem] = []
        self.queue_ids: set[str] = set()
        self._queue_lock = threading.Lock()
        self._disable_webengine = disable_webengine
        
        # Scraper state
        self.current_sort = "toprated"
        self.current_page = 1
        self.current_search = ""
        self.current_workshop_page: Optional[WorkshopPage] = None
        self.mod_cards: list[ModCard] = []
        self._fetcher_thread: Optional[WorkshopFetcherThread] = None
        
        self._setup_ui()
    
    def cleanup(self):
        """Clean up resources."""
        if self._fetcher_thread and self._fetcher_thread.isRunning():
            self._fetcher_thread.wait()
    
    def closeEvent(self, event):
        self.cleanup()
        super().closeEvent(event)
    
    def _setup_ui(self):
        """Set up the browser UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side - Mod browser
        browser_widget = QWidget()
        browser_layout = QVBoxLayout(browser_widget)
        browser_layout.setContentsMargins(4, 4, 4, 4)
        
        # Search bar
        search_bar = QHBoxLayout()
        
        self.btn_back = QPushButton("←")
        self.btn_back.setFixedWidth(30)
        self.btn_back.setToolTip("Previous page")
        self.btn_back.clicked.connect(self._prev_page)
        search_bar.addWidget(self.btn_back)
        
        self.btn_forward = QPushButton("→")
        self.btn_forward.setFixedWidth(30)
        self.btn_forward.setToolTip("Next page")
        self.btn_forward.clicked.connect(self._next_page)
        search_bar.addWidget(self.btn_forward)
        
        self.btn_refresh = QPushButton("🔄")
        self.btn_refresh.setFixedWidth(30)
        self.btn_refresh.setToolTip("Refresh")
        self.btn_refresh.clicked.connect(lambda: self._fetch_workshop())
        search_bar.addWidget(self.btn_refresh)
        
        self.btn_home = QPushButton("🏠")
        self.btn_home.setFixedWidth(30)
        self.btn_home.setToolTip("Workshop home")
        self.btn_home.clicked.connect(lambda: self._open_in_browser(self.WORKSHOP_URL))
        search_bar.addWidget(self.btn_home)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search Workshop mods...")
        self.search_input.returnPressed.connect(self._do_search)
        search_bar.addWidget(self.search_input, 1)
        
        self.btn_search = QPushButton("🔍")
        self.btn_search.setFixedWidth(30)
        self.btn_search.clicked.connect(self._do_search)
        search_bar.addWidget(self.btn_search)
        
        browser_layout.addLayout(search_bar)
        
        # Category buttons
        cats_layout = QHBoxLayout()
        
        btn_popular = QPushButton("🔥 Most Popular")
        btn_popular.clicked.connect(lambda: self._set_sort("toprated"))
        cats_layout.addWidget(btn_popular)
        
        btn_recent = QPushButton("🆕 Most Recent")
        btn_recent.clicked.connect(lambda: self._set_sort("mostrecent"))
        cats_layout.addWidget(btn_recent)
        
        btn_trending = QPushButton("📈 Trending")
        btn_trending.clicked.connect(lambda: self._set_sort("trend"))
        cats_layout.addWidget(btn_trending)
        
        btn_open_steam = QPushButton("🌐 Open in Browser")
        btn_open_steam.clicked.connect(lambda: self._open_in_browser(self.WORKSHOP_URL))
        cats_layout.addWidget(btn_open_steam)
        
        cats_layout.addStretch()
        browser_layout.addLayout(cats_layout)
        
        # Page info
        self.page_info_label = QLabel("Loading...")
        self.page_info_label.setStyleSheet("color: #a6adc8; font-size: 12px; padding: 4px 0;")
        browser_layout.addWidget(self.page_info_label)
        
        # Scrollable mod cards area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #181825;
            }
        """)
        
        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(8)
        self.cards_layout.addStretch()
        
        self.scroll_area.setWidget(self.cards_container)
        browser_layout.addWidget(self.scroll_area, 1)
        
        # Loading indicator
        self.loading_label = QLabel("⏳ Loading workshop data...")
        self.loading_label.setStyleSheet("color: #89b4fa; font-size: 13px; padding: 20px;")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        browser_layout.addWidget(self.loading_label)
        
        splitter.addWidget(browser_widget)
        
        # Right side - Queue (same as before)
        queue_widget = QWidget()
        queue_widget.setMaximumWidth(350)
        queue_widget.setMinimumWidth(250)
        queue_layout = QVBoxLayout(queue_widget)
        queue_layout.setContentsMargins(4, 4, 4, 4)
        
        queue_header = QHBoxLayout()
        queue_header.addWidget(QLabel("📥 Download Queue"))
        queue_header.addStretch()
        self.queue_count = QLabel("(0)")
        queue_header.addWidget(self.queue_count)
        queue_layout.addLayout(queue_header)
        
        self.queue_list = QListWidget()
        self.queue_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        queue_layout.addWidget(self.queue_list, 1)
        
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
        
        self.dup_check = QCheckBox("Skip already downloaded mods")
        self.dup_check.setChecked(True)
        queue_layout.addWidget(self.dup_check)
        
        batch_group = QGroupBox("Batch Add (IDs/URLs)")
        batch_layout = QVBoxLayout(batch_group)
        
        self.batch_input = QTextEdit()
        self.batch_input.setMaximumHeight(80)
        self.batch_input.setPlaceholderText("Paste multiple mod IDs or URLs here (one per line)")
        batch_layout.addWidget(self.batch_input)
        
        batch_btns = QHBoxLayout()
        self.btn_add_batch = QPushButton("Add All")
        self.btn_add_batch.clicked.connect(self._add_batch)
        batch_btns.addWidget(self.btn_add_batch)
        
        self.btn_parse_collection = QPushButton("Parse Collection")
        self.btn_parse_collection.clicked.connect(self._parse_collection)
        batch_btns.addWidget(self.btn_parse_collection)
        batch_layout.addLayout(batch_btns)
        queue_layout.addWidget(batch_group)
        
        self.btn_download = QPushButton("⬇️ Download All")
        self.btn_download.setStyleSheet("background-color: #2a5a2a; font-weight: bold; padding: 8px;")
        self.btn_download.clicked.connect(self._start_download)
        queue_layout.addWidget(self.btn_download)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        queue_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #888;")
        queue_layout.addWidget(self.status_label)
        
        splitter.addWidget(queue_widget)
        splitter.setSizes([700, 300])
        
        layout.addWidget(splitter, 1)
    
    def _set_sort(self, sort: str):
        """Change sort order and reload."""
        self.current_sort = sort
        self.current_page = 1
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
        )
        self._fetcher_thread.finished.connect(self._on_fetch_finished)
        self._fetcher_thread.error.connect(self._on_fetch_error)
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
            card = ModCard(mod, self.downloaded_ids)
            card.add_requested.connect(self._add_to_queue_from_card)
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)
            self.mod_cards.append(card)
            # Load thumbnails asynchronously
            card.load_thumbnail()
        
        QApplication.processEvents()
    
    def _on_fetch_error(self, error: str):
        """Handle fetch error."""
        self.loading_label.setText(f"❌ Error: {error}")
        self.loading_label.setStyleSheet("color: #f38ba8; font-size: 13px; padding: 20px;")
        self.btn_refresh.setEnabled(True)
    
    def _add_to_queue_from_card(self, workshop_id: str):
        """Add a mod to queue from card button."""
        # Find the mod data
        if self.current_workshop_page:
            for mod in self.current_workshop_page.mods:
                if mod.workshop_id == workshop_id:
                    self._add_mod_to_queue(mod)
                    break
    
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
            )
            self.queue.append(item)
            self.queue_ids.add(mod.workshop_id)
            
            queue_item = DownloadQueueItem(item)
            self.queue_list.addItem(queue_item)
            self.queue_count.setText(f"({len(self.queue)})")
            
            self.mod_added.emit(mod.workshop_id, mod.name)
    
    def _open_in_browser(self, url: str):
        """Open URL in system browser."""
        QDesktopServices.openUrl(QUrl(url))
    
    def _open_url(self, url: str):
        """Open URL - for compatibility with old interface."""
        # Try to extract workshop ID and add to queue
        match = re.search(r'id=(\d+)', url)
        if match:
            workshop_id = match.group(1)
            self._add_id_to_queue(workshop_id)
        else:
            self._open_in_browser(url)
    
    def _add_id_to_queue(self, workshop_id: str):
        """Add a workshop ID to queue."""
        with self._queue_lock:
            if workshop_id in self.queue_ids:
                return
            
            item = WorkshopItem(workshop_id=workshop_id)
            self.queue.append(item)
            self.queue_ids.add(workshop_id)
            
            queue_item = DownloadQueueItem(item)
            self.queue_list.addItem(queue_item)
            self.queue_count.setText(f"({len(self.queue)})")
    
    def _add_current_to_queue(self):
        """Add current URL/ID to queue (compatibility method)."""
        text = self.search_input.text().strip() if hasattr(self, 'search_input') else ""
        if not text:
            return
        
        # Check if it's a URL
        match = re.search(r'id=(\d+)', text)
        if match:
            self._add_id_to_queue(match.group(1))
        elif text.isdigit():
            self._add_id_to_queue(text)
    
    def _on_url_changed(self, url):
        """Handle URL change (compatibility)."""
        pass
    
    def _navigate_to_url(self):
        """Navigate to URL (compatibility)."""
        self._add_current_to_queue()
    
    # Queue management methods
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
        """Parse a collection URL and add all items."""
        text = self.batch_input.toPlainText().strip()
        match = re.search(r'id=(\d+)', text)
        if match:
            self._add_id_to_queue(match.group(1))
            self.status_label.setText("Collection added to queue (items will be resolved during download)")
    
    def _start_download(self):
        """Start downloading all queued mods."""
        with self._queue_lock:
            ids = [item.workshop_id for item in self.queue]
        
        if not ids:
            self.status_label.setText("Queue is empty!")
            return
        
        self.download_requested.emit(ids)
