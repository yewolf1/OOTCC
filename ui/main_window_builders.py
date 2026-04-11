from __future__ import annotations

from ui.builders_inventory_tabs import MainWindowInventoryTabsBuilderMixin
from ui.builders_progress_tabs import MainWindowProgressTabsBuilderMixin
from ui.builders_right_panel import MainWindowRightPanelBuilderMixin
from ui.builders_runtime_tabs import MainWindowRuntimeTabsBuilderMixin
from ui.builders_shell import MainWindowShellBuilderMixin
from ui.builders_status_tabs import MainWindowStatusTabsBuilderMixin


class MainWindowBuilderMixin(
    MainWindowShellBuilderMixin,
    MainWindowStatusTabsBuilderMixin,
    MainWindowInventoryTabsBuilderMixin,
    MainWindowRuntimeTabsBuilderMixin,
    MainWindowProgressTabsBuilderMixin,
    MainWindowRightPanelBuilderMixin,
):
    """Aggregate UI builder mixin that keeps the public interface unchanged."""

    pass
