from __future__ import annotations

from ui.builders.inventory_tabs import MainWindowInventoryTabsBuilderMixin
from ui.builders.progress_tabs import MainWindowProgressTabsBuilderMixin
from ui.builders.right_panel import MainWindowRightPanelBuilderMixin
from ui.builders.runtime_tabs import MainWindowRuntimeTabsBuilderMixin
from ui.builders.shell import MainWindowShellBuilderMixin
from ui.builders.status_tabs import MainWindowStatusTabsBuilderMixin


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
