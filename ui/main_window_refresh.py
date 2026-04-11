from __future__ import annotations

from ui.refresh_inventory import MainWindowInventoryRefreshMixin
from ui.refresh_progress import MainWindowProgressRefreshMixin
from ui.refresh_runtime import MainWindowRuntimeRefreshMixin
from ui.refresh_status import MainWindowStatusRefreshMixin


class MainWindowRefreshMixin(
    MainWindowStatusRefreshMixin,
    MainWindowInventoryRefreshMixin,
    MainWindowRuntimeRefreshMixin,
    MainWindowProgressRefreshMixin,
):
    """Aggregate UI refresh mixin that keeps the public interface unchanged."""

    pass
