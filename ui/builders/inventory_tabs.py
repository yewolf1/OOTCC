from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

from core.definitions.inventory_definitions import AMMO_SLOTS, ITEM_SLOTS

"""Builders for inventory and ammo tabs."""

class MainWindowInventoryTabsBuilderMixin:
    def _build_items_tab(self, parent: ctk.CTkFrame) -> None:
        scroll = ctk.CTkScrollableFrame(parent, corner_radius=12)
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(scroll, text="Inventory items", font=ctk.CTkFont(size=22, weight="bold")).pack(
            anchor="w", padx=8, pady=(8, 12)
        )

        for slot, item_def in ITEM_SLOTS.items():
            row = ctk.CTkFrame(scroll, corner_radius=12)
            row.pack(fill="x", padx=6, pady=4)

            row.grid_columnconfigure(0, weight=1)
            row.grid_columnconfigure(1, weight=0)

            current_var = tk.StringVar(value="0")
            self.item_vars[slot] = current_var

            slot_label = item_def["label"]
            choices = item_def["choices"]

            left_info = ctk.CTkFrame(row, fg_color="transparent")
            left_info.grid(row=0, column=0, sticky="ew", padx=(10, 8), pady=10)
            left_info.grid_columnconfigure(0, weight=0)
            left_info.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(
                left_info,
                text=f"[{slot:02}] {slot_label}",
                anchor="w",
                width=220,
            ).grid(row=0, column=0, sticky="w", padx=(0, 12))

            ctk.CTkLabel(
                left_info,
                textvariable=current_var,
                anchor="w",
                width=180,
            ).grid(row=0, column=1, sticky="w")

            right_actions = ctk.CTkFrame(row, fg_color="transparent")
            right_actions.grid(row=0, column=1, sticky="e", padx=(8, 10), pady=10)

            choice_map: dict[str, int] = {}
            choice_labels: list[str] = []

            for raw_value, label in choices.items():
                display = f"{raw_value} - {label}"
                choice_labels.append(display)
                choice_map[display] = raw_value

            self.item_choice_maps[slot] = choice_map

            select_var = tk.StringVar(value=choice_labels[0])
            self.item_select_vars[slot] = select_var

            ctk.CTkComboBox(
                right_actions,
                values=choice_labels,
                variable=select_var,
                width=200,
            ).grid(row=0, column=0, padx=(0, 10), sticky="e")

            ctk.CTkButton(
                right_actions,
                text="Apply",
                width=80,
                command=lambda s=slot: self.apply_item_value(s),
            ).grid(row=0, column=1, padx=(0, 8))

            ctk.CTkButton(
                right_actions,
                text="Clear",
                width=80,
                command=lambda s=slot: self.clear_item_slot(s),
            ).grid(row=0, column=2)

    def _build_ammo_tab(self, parent: ctk.CTkFrame) -> None:
        scroll = ctk.CTkScrollableFrame(parent, corner_radius=12)
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(scroll, text="Ammo / quantities", font=ctk.CTkFont(size=22, weight="bold")).pack(
            anchor="w", padx=8, pady=(8, 12)
        )

        for slot, name in AMMO_SLOTS.items():
            row = ctk.CTkFrame(scroll, corner_radius=12)
            row.pack(fill="x", padx=6, pady=4)
            row.grid_columnconfigure(1, weight=1)

            value_var = tk.StringVar(value="0")
            self.ammo_vars[slot] = value_var

            ctk.CTkLabel(row, text=f"[{slot:02}] {name}", width=220, anchor="w").grid(
                row=0,
                column=0,
                padx=10,
                pady=10,
                sticky="w",
            )
            ctk.CTkEntry(row, textvariable=value_var, width=90).grid(
                row=0,
                column=1,
                padx=10,
                pady=10,
                sticky="w",
            )
            ctk.CTkButton(
                row,
                text="Set",
                width=70,
                command=lambda s=slot: self.apply_ammo_slot(s),
            ).grid(row=0, column=2, padx=10, pady=10)
            ctk.CTkButton(
                row,
                text="Zero",
                width=70,
                command=lambda s=slot: self.zero_ammo_slot(s),
            ).grid(row=0, column=3, padx=(0, 10), pady=10)
