"""
UI Package for RimModManager
"""

from .mod_widgets import (
    ModListItem,
    ModSearchFilter,
    DraggableModList,
    ModDetailsPanel,
    ModListControls,
    ConflictWarningWidget
)
from .main_window import MainWindow
# LAZY IMPORT: WorkshopBrowser loaded on-demand to save memory
# from .workshop_browser import WorkshopBrowser, WorkshopDownloadDialog
from .download_manager import DownloadLogWidget, SteamCMDChecker
from .profiles_manager import ProfilesManagerWidget, ProfilesTab, BackupsTab, ImportExportTab
from .tools_widgets import (
    ToolsTabWidget,
    ModUpdateCheckerWidget,
    ConflictResolverWidget,
    EnhancedModInfoWidget
)
from .graph_view import (
    ConflictGraphDialog,
    ModGraphView,
    EdgeType
)

__all__ = [
    'ModListItem',
    'ModSearchFilter',
    'DraggableModList',
    'ModDetailsPanel',
    'ModListControls',
    'ConflictWarningWidget',
    'MainWindow',
    # 'WorkshopBrowser',  # Lazy loaded
    # 'WorkshopDownloadDialog',  # Lazy loaded
    'DownloadLogWidget',
    'SteamCMDChecker',
    'ProfilesManagerWidget',
    'ProfilesTab',
    'BackupsTab',
    'ImportExportTab',
    'ToolsTabWidget',
    'ModUpdateCheckerWidget',
    'ConflictResolverWidget',
    'EnhancedModInfoWidget',
    'ConflictGraphDialog',
    'ModGraphView',
    'EdgeType',
]
