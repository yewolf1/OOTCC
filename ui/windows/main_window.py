from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

from core.controllers.app_controller import AppController
from services.view_model.bridge_presenter import BridgePresenter
from ui.windows.main_window_builders import MainWindowBuilderMixin
from ui.windows.main_window_commands import MainWindowCommandMixin
from ui.windows.main_window_helpers import MainWindowHelperMixin
from ui.windows.main_window_render import MainWindowRenderMixin
from twitch.reward_catalog import REWARD_UI_HELP


class MainWindow(
    MainWindowHelperMixin,
    MainWindowBuilderMixin,
    MainWindowRenderMixin,
    MainWindowCommandMixin,
    ctk.CTk,
):
    def __init__(self) -> None:
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.app_metadata = self._load_app_metadata()
        self.title(self._app_display_title())
        self.geometry("1520x940")
        self.minsize(1320, 860)

        self.controller = AppController(self._base_dir())
        self.presenter = BridgePresenter(self, self.controller)

        self.status_var = tk.StringVar(value="Not attached")
        self.build_var = tk.StringVar(value="Unknown build")
        self.hearts_var = tk.StringVar(value="0.00 / 0.00 hearts")
        self.message_var = tk.StringVar(value="Waiting for refresh")

        self.health_slider_var = tk.DoubleVar(value=3.0)
        self.max_health_slider_var = tk.DoubleVar(value=3.0)

        self.health_summary_var = tk.StringVar(value="Health unavailable")
        self.rupees_var = tk.StringVar(value="0")
        self.rupees_summary_var = tk.StringVar(value="Rupees unavailable")
        self.magic_current_var = tk.StringVar(value="0")
        self.magic_level_var = tk.StringVar(value="No magic")
        self.magic_summary_var = tk.StringVar(value="Magic unavailable")
        self.button_summary_var = tk.StringVar(value="Buttons unavailable")
        self.teleport_summary_var = tk.StringVar(value="Runtime teleport unavailable")
        self.link_state_summary_var = tk.StringVar(value="Link state unavailable")
        self.link_bridge_summary_var = tk.StringVar(value="DLL bridge unavailable")

        self.equipment_var = tk.StringVar(value="0")
        self.upgrades_var = tk.StringVar(value="0")
        self.quest_items_var = tk.StringVar(value="0")
        self.equips_equipment_var = tk.StringVar(value="0")
        self.inventory_equipment_var = tk.StringVar(value="0")
        self.equipment_summary_var = tk.StringVar(value="Equipment snapshot unavailable")

        self.item_vars: dict[int, tk.StringVar] = {}
        self.ammo_vars: dict[int, tk.StringVar] = {}
        self.item_select_vars: dict[int, tk.StringVar] = {}
        self.item_choice_maps: dict[int, dict[str, int]] = {}

        self.equipment_entry_vars: dict[str, tk.StringVar] = {}
        self.equipment_group_vars: dict[str, tk.StringVar] = {}
        self.upgrade_level_vars: dict[str, tk.StringVar] = {}

        self.quest_flag_vars: dict[str, tk.BooleanVar] = {}
        self.quest_flag_checkboxes: dict[str, ctk.CTkCheckBox] = {}
        self.button_value_vars: dict[str, tk.StringVar] = {}
        self.button_select_vars: dict[str, tk.StringVar] = {}
        self.button_choice_maps: dict[str, dict[str, str]] = {}
        self.sword_mode_var = tk.StringVar(value="Swordless")
        self.teleport_status_vars: dict[str, tk.StringVar] = {}
        self.teleport_random_result_var = tk.StringVar(value="Random pool not loaded")
        self.link_player_address_var = tk.StringVar(value="")
        self.link_burn_value_var = tk.StringVar(value="120")
        self.link_freeze_value_var = tk.StringVar(value="40")
        self.link_shock_value_var = tk.StringVar(value="40")

        self.twitch_status_var = tk.StringVar(value="Disconnected")
        self.twitch_config_path_var = tk.StringVar(value="")
        self.twitch_channel_login_var = tk.StringVar(value="")
        self.twitch_last_event_var = tk.StringVar(value="No Twitch redeem received yet")
        first_reward = next(iter(REWARD_UI_HELP))
        self.twitch_test_reward_var = tk.StringVar(value=first_reward)
        self.twitch_test_reward_help_var = tk.StringVar(value=REWARD_UI_HELP[first_reward])
        self.twitch_test_input_var = tk.StringVar(value="")
        self.twitch_test_user_var = tk.StringVar(value="viewer_test")

        self.twitch_test_reward_var.trace_add("write", self._on_twitch_reward_changed)

        self.current_log_lines: list[str] = []
        self.log_window = None
        self.log_window_box = None
        self.overlay_window = None
        self.overlay_title_label = None
        self.overlay_rows: list[dict[str, ctk.CTkBaseClass]] = []

        self._build_layout()
        self.presenter.initialize()
        self.after(250, self._overlay_tick)
        self.after(3000, self._auto_refresh_state)

    def _on_twitch_reward_changed(self, *_args) -> None:
        reward = self.twitch_test_reward_var.get()
        self.twitch_test_reward_help_var.set(REWARD_UI_HELP.get(reward, "No help available."))

    def open_log_window(self) -> None:
        if self.log_window is not None and self.log_window.winfo_exists():
            self.log_window.deiconify()
            self.log_window.lift()
            self.log_window.focus_force()
            self._sync_log_window()
            return

        self.log_window = ctk.CTkToplevel(self)
        self.log_window.title("Bridge log")
        self.log_window.geometry("980x620")
        self.log_window.minsize(760, 420)
        self.log_window.grid_columnconfigure(0, weight=1)
        self.log_window.grid_rowconfigure(1, weight=1)
        self.log_window.protocol("WM_DELETE_WINDOW", self._close_log_window)

        ctk.CTkLabel(
            self.log_window,
            text="Bridge log",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).grid(row=0, column=0, padx=16, pady=(16, 8), sticky="w")

        self.log_window_box = ctk.CTkTextbox(self.log_window)
        self.log_window_box.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="nsew")
        self._sync_log_window()

    def _close_log_window(self) -> None:
        if self.log_window is not None and self.log_window.winfo_exists():
            self.log_window.destroy()
        self.log_window = None
        self.log_window_box = None

    def _sync_log_window(self) -> None:
        if self.log_window_box is None or not self.log_window_box.winfo_exists():
            return
        self.log_window_box.configure(state="normal")
        self.log_window_box.delete("1.0", "end")
        self.log_window_box.insert("end", "\n".join(self.current_log_lines))
        self.log_window_box.see("end")
        self.log_window_box.configure(state="disabled")


    def open_twitch_overlay(self) -> None:
        if self.overlay_window is not None and self.overlay_window.winfo_exists():
            self.overlay_window.deiconify()
            self.overlay_window.lift()
            self.overlay_window.focus_force()
            self._sync_twitch_overlay()
            return

        self.overlay_window = ctk.CTkToplevel(self)
        self.overlay_window.title("SoH Twitch Overlay")
        self.overlay_window.geometry("360x560+100+100")
        self.overlay_window.minsize(320, 420)
        self.overlay_window.attributes("-topmost", True)
        self.overlay_window.attributes("-alpha", 0.94)
        self.overlay_window.configure(fg_color="#020617")
        self.overlay_window.grid_columnconfigure(0, weight=1)
        self.overlay_window.protocol("WM_DELETE_WINDOW", self._close_twitch_overlay)

        container = ctk.CTkFrame(self.overlay_window, fg_color="#020617")
        container.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        container.grid_columnconfigure(0, weight=1)

        self.overlay_title_label = ctk.CTkLabel(
            container,
            text="Active Twitch effects",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#E5E7EB",
        )
        self.overlay_title_label.grid(row=0, column=0, sticky="w", padx=6, pady=(0, 8))

        self.overlay_rows = []
        for row_index in range(8):
            card = ctk.CTkFrame(container, corner_radius=14, fg_color="#0F172A")
            card.grid(row=row_index + 1, column=0, sticky="ew", padx=4, pady=4)
            card.grid_columnconfigure(0, weight=1)

            viewer_label = ctk.CTkLabel(
                card,
                text="",
                anchor="w",
                justify="left",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="#C4B5FD",
            )
            viewer_label.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 0))

            effect_label = ctk.CTkLabel(
                card,
                text="",
                anchor="w",
                justify="left",
                font=ctk.CTkFont(size=15, weight="bold"),
                text_color="#F8FAFC",
            )
            effect_label.grid(row=1, column=0, sticky="ew", padx=10, pady=(2, 0))

            detail_label = ctk.CTkLabel(
                card,
                text="",
                anchor="w",
                justify="left",
                font=ctk.CTkFont(size=13),
                text_color="#94A3B8",
            )
            detail_label.grid(row=2, column=0, sticky="ew", padx=10, pady=(2, 8))

            self.overlay_rows.append({
                'frame': card,
                'viewer': viewer_label,
                'effect': effect_label,
                'detail': detail_label,
            })

        self._sync_twitch_overlay()

    def _close_twitch_overlay(self) -> None:
        if self.overlay_window is not None and self.overlay_window.winfo_exists():
            self.overlay_window.destroy()
        self.overlay_window = None
        self.overlay_title_label = None
        self.overlay_rows = []

    def _sync_twitch_overlay(self) -> None:
        if self.overlay_window is None or not self.overlay_window.winfo_exists() or self.overlay_title_label is None:
            return

        entries = self.controller.get_twitch_overlay_entries()
        if entries:
            self.overlay_title_label.configure(text=f"Twitch redeems ({len(entries)})")
        else:
            self.overlay_title_label.configure(text="No recent Twitch redeem")

        for idx, row in enumerate(self.overlay_rows):
            if idx < len(entries):
                entry = entries[idx]
                row['frame'].grid()
                viewer = str(entry.get('viewer', '')).strip()
                title = str(entry.get('title', '')).strip()
                detail = str(entry.get('detail', '')).strip()
                remaining_seconds = int(entry.get('remaining_seconds', 0))
                row['viewer'].configure(text=viewer if viewer else "Viewer")
                row['effect'].configure(text=title)
                row['detail'].configure(text=f"{detail} ({remaining_seconds}s)" if detail else f"{remaining_seconds}s")
            else:
                row['frame'].grid_remove()

    def _overlay_tick(self) -> None:
        try:
            if self.overlay_window is not None and self.overlay_window.winfo_exists():
                self._sync_twitch_overlay()
        finally:
            self.after(250, self._overlay_tick)
