from __future__ import annotations


"""Top-level refresh orchestration and log rendering helpers."""

class MainWindowStatusRefreshMixin:
    def refresh_state(self) -> None:
        self._refresh_state_with_runtime_scan(False)

    def force_refresh_state(self) -> None:
        self._refresh_state_with_runtime_scan(True)

    def _refresh_state_with_runtime_scan(self, force_runtime_scan: bool) -> None:
        self.health_state = self.controller.refresh(force_runtime_scan=force_runtime_scan)
        self.status_var.set("Attached" if self.health_state.attached else "Offline")
        self.build_var.set(self.health_state.version_label)
        self.hearts_var.set(f"{self.health_state.current_hearts:.2f} / {self.health_state.max_hearts:.2f} hearts")
        self.message_var.set(self.health_state.message)

        ui_max = max(3.0, self.health_state.max_hearts, 20.0)

        self.health_slider.configure(to=ui_max, number_of_steps=max(48, int(ui_max * 16)))
        self.health_slider_var.set(max(0.0, self.health_state.current_hearts))

        self.max_health_slider.configure(to=max(20.0, self.health_state.max_hearts + 5.0), number_of_steps=320)
        self.max_health_slider_var.set(max(1.0, self.health_state.max_hearts))

        self._refresh_health_ui()
        self._refresh_rupees_ui()
        self._refresh_inventory_ui()
        self._refresh_flags_ui()
        self._refresh_magic_ui()
        self._refresh_equipment_ui()
        self._refresh_buttons_ui()
        self._refresh_teleport_ui()
        self._refresh_quest_status_ui()
        self._render_logs()

    def _render_logs(self) -> None:
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.insert("end", "\n".join(self.controller.log_lines()))
        self.log_box.configure(state="disabled")
