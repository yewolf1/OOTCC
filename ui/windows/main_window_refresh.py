from __future__ import annotations

from ui.refresh.inventory import MainWindowInventoryRefreshMixin
from ui.refresh.progress import MainWindowProgressRefreshMixin
from ui.refresh.runtime import MainWindowRuntimeRefreshMixin
from ui.refresh.status import MainWindowStatusRefreshMixin


class MainWindowRefreshMixin(
    MainWindowStatusRefreshMixin,
    MainWindowInventoryRefreshMixin,
    MainWindowRuntimeRefreshMixin,
    MainWindowProgressRefreshMixin,
):
    """Aggregate UI refresh mixin that keeps the public interface unchanged."""

    pass
