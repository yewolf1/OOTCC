from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

from core.definitions.inventory_definitions import QUEST_FLAGS, UPGRADE_GROUPS

"""Builders for progression-oriented tabs such as equipment and quest status."""

class MainWindowProgressTabsBuilderMixin:
    def _build_equipment_tab(self, parent: ctk.CTkFrame) -> None:
        scroll = ctk.CTkScrollableFrame(parent, corner_radius=12)
        scroll.pack(fill="both", expand=True, padx=10, pady=10)
        scroll.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(scroll, text="Equipment", font=ctk.CTkFont(size=22, weight="bold")).grid(
            row=0, column=0, columnspan=2, padx=8, pady=(8, 2), sticky="w"
        )
        ctk.CTkLabel(scroll, textvariable=self.equipment_summary_var, justify="left").grid(
            row=1, column=0, columnspan=2, padx=8, pady=(0, 14), sticky="w"
        )

        equipment_groups = [item for item in self._equipment_groups_items()]
        for index, (group_key, group) in enumerate(equipment_groups):
            row = (index // 2) + 2
            column = index % 2

            card = ctk.CTkFrame(scroll, corner_radius=12)
            card.grid(row=row, column=column, padx=8, pady=8, sticky="nsew")
            card.grid_columnconfigure(0, weight=1)

            group_var = tk.StringVar(value="No data")
            self.equipment_group_vars[group_key] = group_var

            ctk.CTkLabel(card, text=group["label"], font=ctk.CTkFont(size=18, weight="bold")).grid(
                row=0, column=0, padx=12, pady=(12, 4), sticky="w"
            )
            ctk.CTkLabel(card, textvariable=group_var, justify="left").grid(
                row=1, column=0, padx=12, pady=(0, 10), sticky="w"
            )

            for entry_index, (item_key, entry) in enumerate(self._equipment_entries_items(group), start=2):
                entry_var = tk.StringVar(value="Unknown")
                self.equipment_entry_vars[item_key] = entry_var

                row_frame = ctk.CTkFrame(card, fg_color="transparent")
                row_frame.grid(row=entry_index, column=0, padx=12, pady=4, sticky="ew")
                row_frame.grid_columnconfigure(0, weight=1)

                ctk.CTkLabel(row_frame, text=entry["label"], anchor="w").grid(
                    row=0, column=0, sticky="w", padx=(0, 10)
                )
                ctk.CTkLabel(row_frame, textvariable=entry_var, width=110, anchor="w").grid(
                    row=0, column=1, sticky="w", padx=(0, 10)
                )
                ctk.CTkButton(
                    row_frame,
                    text="Add",
                    width=60,
                    command=lambda g=group_key, k=item_key: self.add_equipment_item(g, k),
                ).grid(row=0, column=2, padx=(0, 6))
                ctk.CTkButton(
                    row_frame,
                    text="Remove",
                    width=80,
                    command=lambda g=group_key, k=item_key: self.remove_equipment_item(g, k),
                ).grid(row=0, column=3, padx=(0, 6))
                ctk.CTkButton(
                    row_frame,
                    text="Equip",
                    width=70,
                    command=lambda g=group_key, k=item_key: self.equip_equipment_item(g, k),
                ).grid(row=0, column=4)

        upgrade_base_row = ((len(equipment_groups) + 1) // 2) + 2
        upgrade_card = ctk.CTkFrame(scroll, corner_radius=12)
        upgrade_card.grid(row=upgrade_base_row, column=0, columnspan=2, padx=8, pady=8, sticky="ew")
        upgrade_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(upgrade_card, text="Upgrades", font=ctk.CTkFont(size=18, weight="bold")).grid(
            row=0, column=0, padx=12, pady=(12, 10), sticky="w"
        )

        for row_index, (upgrade_key, group) in enumerate(self._upgrade_groups_items(), start=1):
            level_var = tk.StringVar(value="Unknown")
            self.upgrade_level_vars[upgrade_key] = level_var

            row_frame = ctk.CTkFrame(upgrade_card, fg_color="transparent")
            row_frame.grid(row=row_index, column=0, padx=12, pady=4, sticky="ew")
            row_frame.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(row_frame, text=group["label"], width=140, anchor="w").grid(
                row=0, column=0, sticky="w", padx=(0, 10)
            )
            ctk.CTkLabel(row_frame, textvariable=level_var, anchor="w").grid(
                row=0, column=1, sticky="w", padx=(0, 10)
            )
            ctk.CTkButton(
                row_frame,
                text="-",
                width=40,
                command=lambda k=upgrade_key: self.decrease_upgrade_level(k),
            ).grid(row=0, column=2, padx=(0, 6))
            ctk.CTkButton(
                row_frame,
                text="+",
                width=40,
                command=lambda k=upgrade_key: self.increase_upgrade_level(k),
            ).grid(row=0, column=3)

    def _build_quest_status_tab(self, parent: ctk.CTkFrame) -> None:
        scroll = ctk.CTkScrollableFrame(parent, corner_radius=12)
        scroll.pack(fill="both", expand=True, padx=10, pady=10)
        scroll.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(scroll, text="Quest Status", font=ctk.CTkFont(size=22, weight="bold")).grid(
            row=0, column=0, columnspan=2, padx=8, pady=(8, 12), sticky="w"
        )

        current_row = 1
        group_items = list(QUEST_FLAGS.items())

        for index, (group_key, group_flags) in enumerate(group_items):
            card = ctk.CTkFrame(scroll, corner_radius=12)
            card.grid(row=current_row + (index // 2), column=index % 2, padx=8, pady=8, sticky="nsew")
            card.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                card,
                text=self._quest_group_title(group_key),
                font=ctk.CTkFont(size=18, weight="bold"),
            ).grid(row=0, column=0, padx=12, pady=(12, 10), sticky="w")

            for row_index, flag_key in enumerate(group_flags.keys(), start=1):
                var = tk.BooleanVar(value=False)
                self.quest_flag_vars[flag_key] = var

                checkbox = ctk.CTkCheckBox(
                    card,
                    text=self._quest_flag_title(flag_key),
                    variable=var,
                    command=lambda k=flag_key: self.toggle_quest_flag(k),
                )
                checkbox.grid(row=row_index, column=0, padx=12, pady=6, sticky="w")
                self.quest_flag_checkboxes[flag_key] = checkbox

    def _build_flags_tab(self, parent: ctk.CTkFrame) -> None:
        frame = ctk.CTkScrollableFrame(parent, corner_radius=12)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(frame, text="Equipped mask (u16)", font=ctk.CTkFont(size=20, weight="bold")).grid(
            row=0, column=0, columnspan=3, padx=12, pady=(14, 8), sticky="w"
        )
        ctk.CTkEntry(frame, textvariable=self.equips_equipment_var, width=160).grid(
            row=1, column=0, padx=12, pady=8, sticky="w"
        )
        ctk.CTkButton(frame, text="Apply", command=self.apply_equips_equipment).grid(
            row=1, column=1, padx=8, pady=8, sticky="w"
        )

        ctk.CTkLabel(frame, text="Owned equipment mask (u16)", font=ctk.CTkFont(size=20, weight="bold")).grid(
            row=2, column=0, columnspan=3, padx=12, pady=(18, 8), sticky="w"
        )
        ctk.CTkEntry(frame, textvariable=self.inventory_equipment_var, width=160).grid(
            row=3, column=0, padx=12, pady=8, sticky="w"
        )
        ctk.CTkButton(frame, text="Apply", command=self.apply_inventory_equipment).grid(
            row=3, column=1, padx=8, pady=8, sticky="w"
        )

        ctk.CTkLabel(frame, text="Legacy equipment field (u16)", font=ctk.CTkFont(size=20, weight="bold")).grid(
            row=4, column=0, columnspan=3, padx=12, pady=(18, 8), sticky="w"
        )
        ctk.CTkEntry(frame, textvariable=self.equipment_var, width=160).grid(
            row=5, column=0, padx=12, pady=8, sticky="w"
        )
        ctk.CTkButton(frame, text="Apply", command=self.apply_equipment).grid(
            row=5, column=1, padx=8, pady=8, sticky="w"
        )

        ctk.CTkLabel(frame, text="Upgrades (u32)", font=ctk.CTkFont(size=20, weight="bold")).grid(
            row=6, column=0, columnspan=3, padx=12, pady=(18, 8), sticky="w"
        )
        ctk.CTkEntry(frame, textvariable=self.upgrades_var, width=160).grid(
            row=7, column=0, padx=12, pady=8, sticky="w"
        )
        ctk.CTkButton(frame, text="Apply", command=self.apply_upgrades).grid(
            row=7, column=1, padx=8, pady=8, sticky="w"
        )

        ctk.CTkLabel(frame, text="Quest items (u32)", font=ctk.CTkFont(size=20, weight="bold")).grid(
            row=8, column=0, columnspan=3, padx=12, pady=(18, 8), sticky="w"
        )
        ctk.CTkEntry(frame, textvariable=self.quest_items_var, width=160).grid(
            row=9, column=0, padx=12, pady=8, sticky="w"
        )
        ctk.CTkButton(frame, text="Apply", command=self.apply_quest_items).grid(
            row=9, column=1, padx=8, pady=8, sticky="w"
        )
