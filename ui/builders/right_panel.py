from __future__ import annotations

import tkinter as tk

import customtkinter as ctk
from twitch.reward_catalog import REWARD_UI_HELP


"""Builders for the right side widgets such as Twitch controls and logs."""


class MainWindowRightPanelBuilderMixin:
    def _build_right_panel(self, parent: ctk.CTkFrame) -> None:
        scroll = ctk.CTkScrollableFrame(parent, corner_radius=0, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=0, pady=0)
        scroll.grid_columnconfigure(0, weight=1)

        twitch = ctk.CTkFrame(scroll, corner_radius=16)
        twitch.grid(row=0, column=0, sticky="ew", padx=16, pady=16)
        twitch.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(twitch, text="Twitch", font=ctk.CTkFont(size=22, weight="bold")).grid(
            row=0, column=0, columnspan=3, padx=16, pady=(16, 10), sticky="w"
        )

        ctk.CTkLabel(twitch, text="Status", width=110, anchor="w").grid(row=1, column=0, padx=(16, 8), pady=6, sticky="w")
        ctk.CTkLabel(twitch, textvariable=self.twitch_status_var, anchor="w").grid(
            row=1, column=1, columnspan=2, padx=(0, 16), pady=6, sticky="ew"
        )

        ctk.CTkLabel(twitch, text="Channel", width=110, anchor="w").grid(row=2, column=0, padx=(16, 8), pady=6, sticky="w")
        ctk.CTkLabel(twitch, textvariable=self.twitch_channel_login_var, anchor="w").grid(
            row=2, column=1, columnspan=2, padx=(0, 16), pady=6, sticky="ew"
        )

        ctk.CTkLabel(twitch, text="Config file", width=110, anchor="w").grid(row=3, column=0, padx=(16, 8), pady=6, sticky="w")
        ctk.CTkLabel(twitch, textvariable=self.twitch_config_path_var, anchor="w", justify="left", wraplength=360).grid(
            row=3, column=1, columnspan=2, padx=(0, 16), pady=6, sticky="ew"
        )

        ctk.CTkLabel(
            twitch,
            text=(
                "Edit twitch_config.json outside the app, then click Connect.\n"
                "The app does not store channel credentials in the UI anymore."
            ),
            justify="left",
            anchor="w",
        ).grid(row=4, column=0, columnspan=3, padx=16, pady=(4, 8), sticky="ew")

        actions = ctk.CTkFrame(twitch, fg_color="transparent")
        actions.grid(row=5, column=0, columnspan=3, padx=16, pady=(2, 8), sticky="ew")
        for col in range(3):
            actions.grid_columnconfigure(col, weight=1)

        ctk.CTkButton(
            actions,
            text="Connect",
            command=self.connect_twitch,
            fg_color="#16A34A",
            hover_color="#15803D",
        ).grid(row=0, column=0, padx=4, pady=4, sticky="ew")
        ctk.CTkButton(
            actions,
            text="Disconnect",
            command=self.disconnect_twitch,
            fg_color="#DC2626",
            hover_color="#B91C1C",
        ).grid(row=0, column=1, padx=4, pady=4, sticky="ew")
        ctk.CTkButton(
            actions,
            text="Reset tokens",
            command=self.reset_twitch_tokens,
            fg_color="#475569",
            hover_color="#334155",
        ).grid(row=0, column=2, padx=4, pady=4, sticky="ew")

        ctk.CTkLabel(twitch, text="Last redeem", font=ctk.CTkFont(size=18, weight="bold")).grid(
            row=6, column=0, columnspan=3, padx=16, pady=(10, 4), sticky="w"
        )
        ctk.CTkLabel(twitch, textvariable=self.twitch_last_event_var, justify="left", anchor="w").grid(
            row=7, column=0, columnspan=3, padx=16, pady=(0, 10), sticky="ew"
        )

        ctk.CTkLabel(twitch, text="Redeem test", font=ctk.CTkFont(size=18, weight="bold")).grid(
            row=8, column=0, columnspan=3, padx=16, pady=(4, 4), sticky="w"
        )

        reward_options = list(REWARD_UI_HELP.keys())
        ctk.CTkComboBox(twitch, values=reward_options, variable=self.twitch_test_reward_var).grid(
            row=9, column=0, columnspan=3, padx=16, pady=4, sticky="ew"
        )
        ctk.CTkLabel(twitch, textvariable=self.twitch_test_reward_help_var, justify="left", anchor="w", wraplength=420).grid(
            row=10, column=0, columnspan=3, padx=16, pady=(0, 4), sticky="ew"
        )
        ctk.CTkEntry(twitch, textvariable=self.twitch_test_input_var, placeholder_text="Viewer input").grid(
            row=11, column=0, columnspan=2, padx=(16, 8), pady=4, sticky="ew"
        )
        ctk.CTkEntry(twitch, textvariable=self.twitch_test_user_var, placeholder_text="Viewer name").grid(
            row=11, column=2, padx=(0, 16), pady=4, sticky="ew"
        )
        ctk.CTkButton(twitch, text="Simulate redeem", command=self.simulate_twitch_reward).grid(
            row=12, column=0, columnspan=3, padx=16, pady=(4, 8), sticky="ew"
        )
        ctk.CTkButton(
            twitch,
            text="Open Twitch overlay",
            command=self.open_twitch_overlay,
            fg_color="#7C3AED",
            hover_color="#6D28D9",
        ).grid(row=13, column=0, columnspan=3, padx=16, pady=(0, 16), sticky="ew")

        ble_hr = ctk.CTkFrame(scroll, corner_radius=16)
        ble_hr.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 16))
        ble_hr.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(ble_hr, text="Bluetooth HR", font=ctk.CTkFont(size=22, weight="bold")).grid(
            row=0, column=0, columnspan=3, padx=16, pady=(16, 10), sticky="w"
        )

        live_bpm_card = ctk.CTkFrame(ble_hr, corner_radius=14, fg_color="#0F172A")
        live_bpm_card.grid(row=1, column=0, columnspan=3, padx=16, pady=(0, 10), sticky="ew")
        live_bpm_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            live_bpm_card,
            text="Live heart rate",
            anchor="w",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#C4B5FD",
        ).grid(row=0, column=0, sticky="w", padx=12, pady=(10, 0))
        self.ble_hr_live_bpm_canvas, self.ble_hr_live_bpm_canvas_items = self._create_ble_hr_bpm_canvas(
            live_bpm_card,
            width=170,
            height=62,
            background="#0F172A",
            font_size=42,
        )
        self.ble_hr_live_bpm_canvas.grid(row=1, column=0, sticky="w", padx=12, pady=(2, 0))
        ctk.CTkLabel(
            live_bpm_card,
            text="BPM",
            anchor="w",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#22C55E",
        ).grid(row=1, column=1, sticky="sw", padx=(0, 12), pady=(0, 8))
        ctk.CTkLabel(
            live_bpm_card,
            textvariable=self.ble_hr_live_detail_var,
            anchor="w",
            justify="left",
            font=ctk.CTkFont(size=13),
            text_color="#94A3B8",
        ).grid(row=2, column=0, columnspan=2, sticky="ew", padx=12, pady=(2, 10))

        ctk.CTkLabel(ble_hr, text="Status", width=110, anchor="w").grid(row=2, column=0, padx=(16, 8), pady=6, sticky="w")
        ctk.CTkLabel(ble_hr, textvariable=self.ble_hr_status_var, anchor="w", justify="left", wraplength=360).grid(
            row=2, column=1, columnspan=2, padx=(0, 16), pady=6, sticky="ew"
        )

        ctk.CTkLabel(ble_hr, text="Device", width=110, anchor="w").grid(row=3, column=0, padx=(16, 8), pady=6, sticky="w")
        ctk.CTkLabel(ble_hr, textvariable=self.ble_hr_device_var, anchor="w", justify="left", wraplength=360).grid(
            row=3, column=1, columnspan=2, padx=(0, 16), pady=6, sticky="ew"
        )

        ctk.CTkLabel(ble_hr, text="Last sample", width=110, anchor="w").grid(row=4, column=0, padx=(16, 8), pady=6, sticky="w")
        ctk.CTkLabel(ble_hr, textvariable=self.ble_hr_sample_var, anchor="w").grid(
            row=4, column=1, columnspan=2, padx=(0, 16), pady=6, sticky="ew"
        )

        ctk.CTkLabel(ble_hr, text="Enemy speed", width=110, anchor="w").grid(row=5, column=0, padx=(16, 8), pady=6, sticky="w")
        ctk.CTkLabel(ble_hr, textvariable=self.ble_hr_hyper_state_var, anchor="w", justify="left", wraplength=360).grid(
            row=5, column=1, columnspan=2, padx=(0, 16), pady=6, sticky="ew"
        )

        ctk.CTkLabel(ble_hr, text="Levels", width=110, anchor="w").grid(row=6, column=0, padx=(16, 8), pady=6, sticky="w")
        ctk.CTkLabel(ble_hr, textvariable=self.ble_hr_rule_var, anchor="w", justify="left", wraplength=360).grid(
            row=6, column=1, columnspan=2, padx=(0, 16), pady=6, sticky="ew"
        )

        ctk.CTkLabel(ble_hr, text="Config file", width=110, anchor="w").grid(row=7, column=0, padx=(16, 8), pady=6, sticky="w")
        ctk.CTkLabel(ble_hr, textvariable=self.ble_hr_config_path_var, anchor="w", justify="left", wraplength=360).grid(
            row=7, column=1, columnspan=2, padx=(0, 16), pady=6, sticky="ew"
        )

        ctk.CTkLabel(
            ble_hr,
            text=(
                "Wear the chest strap and moisten the electrodes before connecting.\n"
                "Close phone or fitness apps first: Bluetooth heart-rate straps usually connect to one app at a time."
            ),
            justify="left",
            anchor="w",
        ).grid(row=8, column=0, columnspan=3, padx=16, pady=(4, 8), sticky="ew")

        ctk.CTkLabel(ble_hr, text="Progressive thresholds", font=ctk.CTkFont(size=18, weight="bold")).grid(
            row=9, column=0, columnspan=3, padx=16, pady=(4, 4), sticky="w"
        )

        level_editor = ctk.CTkFrame(ble_hr, fg_color="transparent")
        level_editor.grid(row=10, column=0, columnspan=3, padx=16, pady=(0, 8), sticky="ew")
        level_editor.grid_columnconfigure(1, weight=1)
        level_editor.grid_columnconfigure(2, weight=1)

        ctk.CTkLabel(level_editor, text="", width=40).grid(row=0, column=0, padx=(0, 8), pady=(0, 4), sticky="w")
        ctk.CTkLabel(level_editor, text="BPM >=", anchor="w").grid(row=0, column=1, padx=4, pady=(0, 4), sticky="w")
        ctk.CTkLabel(level_editor, text="Speed %", anchor="w").grid(row=0, column=2, padx=4, pady=(0, 4), sticky="w")

        for index, (bpm_var, speed_var) in enumerate(zip(self.ble_hr_level_bpm_vars, self.ble_hr_level_speed_vars), start=1):
            ctk.CTkLabel(level_editor, text=f"L{index}", width=40).grid(
                row=index, column=0, padx=(0, 8), pady=4, sticky="w"
            )
            ctk.CTkEntry(level_editor, textvariable=bpm_var, placeholder_text="100").grid(
                row=index, column=1, padx=4, pady=4, sticky="ew"
            )
            ctk.CTkEntry(level_editor, textvariable=speed_var, placeholder_text="125").grid(
                row=index, column=2, padx=4, pady=4, sticky="ew"
            )

        ctk.CTkLabel(
            ble_hr,
            text="Leave a row blank to disable it. Saving while connected reapplies the current BPM immediately.",
            justify="left",
            anchor="w",
        ).grid(row=11, column=0, columnspan=3, padx=16, pady=(0, 4), sticky="ew")
        ctk.CTkButton(ble_hr, text="Save speed levels", command=self.save_ble_hr_levels).grid(
            row=12, column=0, columnspan=3, padx=16, pady=(0, 8), sticky="ew"
        )

        ble_hr_actions = ctk.CTkFrame(ble_hr, fg_color="transparent")
        ble_hr_actions.grid(row=13, column=0, columnspan=3, padx=16, pady=(2, 16), sticky="ew")
        for col in range(3):
            ble_hr_actions.grid_columnconfigure(col, weight=1)

        ctk.CTkButton(
            ble_hr_actions,
            text="Connect",
            command=self.connect_ble_hr,
            fg_color="#16A34A",
            hover_color="#15803D",
        ).grid(row=0, column=0, padx=4, pady=4, sticky="ew")
        ctk.CTkButton(
            ble_hr_actions,
            text="Disconnect",
            command=self.disconnect_ble_hr,
            fg_color="#DC2626",
            hover_color="#B91C1C",
        ).grid(row=0, column=1, padx=4, pady=4, sticky="ew")
        ctk.CTkButton(
            ble_hr_actions,
            text="Forget device",
            command=self.clear_ble_hr_preferred_device,
            fg_color="#475569",
            hover_color="#334155",
        ).grid(row=0, column=2, padx=4, pady=4, sticky="ew")
        ctk.CTkButton(
            ble_hr_actions,
            text="Open HR overlay",
            command=self.open_ble_hr_overlay,
            fg_color="#0EA5E9",
            hover_color="#0284C7",
        ).grid(row=1, column=0, columnspan=3, padx=4, pady=(4, 0), sticky="ew")

        log_actions = ctk.CTkFrame(scroll, corner_radius=16)
        log_actions.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 16))
        log_actions.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(log_actions, text="Bridge log", font=ctk.CTkFont(size=20, weight="bold")).grid(
            row=0, column=0, padx=16, pady=(16, 8), sticky="w"
        )
        ctk.CTkButton(log_actions, text="Open bridge log", command=self.open_bridge_log).grid(
            row=1, column=0, padx=16, pady=(0, 16), sticky="ew"
        )
