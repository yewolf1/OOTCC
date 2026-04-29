from __future__ import annotations

import tkinter as tk

import customtkinter as ctk


"""UI shell builders for the main application window."""

class MainWindowShellBuilderMixin:
    def _build_layout(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        wrapper = ctk.CTkFrame(self, corner_radius=0)
        wrapper.grid(row=0, column=0, sticky="nsew")
        wrapper.grid_columnconfigure(0, weight=4)
        wrapper.grid_columnconfigure(1, weight=3)
        wrapper.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(wrapper, height=90, corner_radius=18)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=18, pady=(18, 12))
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(header, text=getattr(self, "app_title", "SoH Bridge V1.0"), font=ctk.CTkFont(size=30, weight="bold")).grid(
            row=0, column=0, padx=20, pady=18, sticky="w"
        )

        actions = ctk.CTkFrame(header, fg_color="transparent")
        actions.grid(row=0, column=2, padx=18, pady=18, sticky="e")

        ctk.CTkButton(actions, text="Refresh", width=140, command=self.force_refresh_state).grid(
            row=0, column=0, padx=(0, 10)
        )
        ctk.CTkButton(actions, text="Full heal", width=140, command=self.full_heal).grid(
            row=0, column=1
        )

        left = ctk.CTkFrame(wrapper, corner_radius=18)
        left.grid(row=1, column=0, sticky="nsew", padx=(18, 9), pady=(0, 18))
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(3, weight=1)

        right = ctk.CTkFrame(wrapper, corner_radius=18)
        right.grid(row=1, column=1, sticky="nsew", padx=(9, 18), pady=(0, 18))
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(2, weight=1)

        self._build_left_panel(left)
        self._build_right_panel(right)

    def _build_left_panel(self, parent: ctk.CTkFrame) -> None:
        info = ctk.CTkFrame(parent, corner_radius=16)
        info.pack(fill="x", padx=16, pady=16)
        info.grid_columnconfigure(1, weight=1)

        rows = [
            ("Status", self.status_var),
            ("Build", self.build_var),
            ("Hearts", self.hearts_var),
            ("Message", self.message_var),
        ]

        for idx, (label, var) in enumerate(rows):
            ctk.CTkLabel(info, text=label, width=90, anchor="w", font=ctk.CTkFont(size=14, weight="bold")).grid(
                row=idx, column=0, padx=16, pady=10, sticky="w"
            )
            ctk.CTkLabel(info, textvariable=var, anchor="w").grid(
                row=idx, column=1, padx=8, pady=10, sticky="w"
            )

        tabs = ctk.CTkTabview(parent, corner_radius=16)
        tabs.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        health_tab = tabs.add("Health")
        rupees_tab = tabs.add("Rupees")
        items_tab = tabs.add("Items")
        ammo_tab = tabs.add("Ammo")
        magic_tab = tabs.add("Magic")
        equipment_tab = tabs.add("Equipment")
        buttons_tab = tabs.add("Buttons")
        teleport_tab = tabs.add("Teleport")
        link_state_tab = tabs.add("Link State")
        quest_status_tab = tabs.add("Quest Status")
        flags_tab = tabs.add("Flags")

        self._build_health_tab(health_tab)
        self._build_rupees_tab(rupees_tab)
        self._build_items_tab(items_tab)
        self._build_ammo_tab(ammo_tab)
        self._build_magic_tab(magic_tab)
        self._build_equipment_tab(equipment_tab)
        self._build_buttons_tab(buttons_tab)
        self._build_teleport_tab(teleport_tab)
        self._build_link_state_tab(link_state_tab)
        self._build_quest_status_tab(quest_status_tab)
        self._build_flags_tab(flags_tab)
