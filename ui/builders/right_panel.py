from __future__ import annotations

import customtkinter as ctk
from twitch.reward_catalog import REWARD_UI_HELP


"""Builders for the right side widgets such as Twitch controls and logs."""


class MainWindowRightPanelBuilderMixin:
    def _build_right_panel(self, parent: ctk.CTkFrame) -> None:
        twitch = ctk.CTkFrame(parent, corner_radius=16)
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

        log_actions = ctk.CTkFrame(parent, corner_radius=16)
        log_actions.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 16))
        log_actions.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(log_actions, text="Bridge log", font=ctk.CTkFont(size=20, weight="bold")).grid(
            row=0, column=0, padx=16, pady=(16, 8), sticky="w"
        )
        ctk.CTkButton(log_actions, text="Open bridge log", command=self.open_bridge_log).grid(
            row=1, column=0, padx=16, pady=(0, 16), sticky="ew"
        )
