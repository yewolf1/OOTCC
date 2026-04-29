from __future__ import annotations

import tkinter as tk

import customtkinter as ctk


"""Builders for health and rupees tabs."""

class MainWindowStatusTabsBuilderMixin:
    def _build_health_tab(self, parent: ctk.CTkFrame) -> None:
        frame = ctk.CTkScrollableFrame(parent, corner_radius=12)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(frame, text="Link health", font=ctk.CTkFont(size=22, weight="bold")).grid(
            row=0, column=0, padx=8, pady=(8, 4), sticky="w"
        )
        ctk.CTkLabel(frame, textvariable=self.health_summary_var, justify="left").grid(
            row=1, column=0, padx=8, pady=(0, 14), sticky="w"
        )

        current_card = ctk.CTkFrame(frame, corner_radius=12)
        current_card.grid(row=2, column=0, padx=8, pady=8, sticky="ew")
        current_card.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkLabel(current_card, text="Current health", font=ctk.CTkFont(size=18, weight="bold")).grid(
            row=0, column=0, columnspan=3, padx=12, pady=(12, 10), sticky="w"
        )
        self.health_slider = ctk.CTkSlider(
            current_card,
            from_=0,
            to=20,
            variable=self.health_slider_var,
            number_of_steps=320,
        )
        self.health_slider.grid(row=1, column=0, columnspan=3, sticky="ew", padx=12, pady=(0, 12))
        ctk.CTkButton(current_card, text="Apply current health", command=self.apply_current_health).grid(
            row=2, column=0, padx=10, pady=(0, 12), sticky="ew"
        )
        ctk.CTkButton(current_card, text="+ 1 heart", command=lambda: self.adjust_current_health(1.0)).grid(
            row=2, column=1, padx=10, pady=(0, 12), sticky="ew"
        )
        ctk.CTkButton(current_card, text="- 1 heart", command=lambda: self.adjust_current_health(-1.0)).grid(
            row=2, column=2, padx=10, pady=(0, 12), sticky="ew"
        )

        max_card = ctk.CTkFrame(frame, corner_radius=12)
        max_card.grid(row=3, column=0, padx=8, pady=8, sticky="ew")
        max_card.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkLabel(max_card, text="Max health", font=ctk.CTkFont(size=18, weight="bold")).grid(
            row=0, column=0, columnspan=3, padx=12, pady=(12, 10), sticky="w"
        )
        self.max_health_slider = ctk.CTkSlider(
            max_card,
            from_=1,
            to=20,
            variable=self.max_health_slider_var,
            number_of_steps=304,
        )
        self.max_health_slider.grid(row=1, column=0, columnspan=3, sticky="ew", padx=12, pady=(0, 12))
        ctk.CTkButton(max_card, text="Apply max health", command=self.apply_max_health).grid(
            row=2, column=0, padx=10, pady=(0, 12), sticky="ew"
        )
        ctk.CTkButton(max_card, text="+ 1 max heart", command=lambda: self.adjust_max_health(1.0)).grid(
            row=2, column=1, padx=10, pady=(0, 12), sticky="ew"
        )
        ctk.CTkButton(max_card, text="- 1 max heart", command=lambda: self.adjust_max_health(-1.0)).grid(
            row=2, column=2, padx=10, pady=(0, 12), sticky="ew"
        )

    def _build_rupees_tab(self, parent: ctk.CTkFrame) -> None:
        frame = ctk.CTkScrollableFrame(parent, corner_radius=12)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(frame, text="Rupees", font=ctk.CTkFont(size=22, weight="bold")).grid(
            row=0, column=0, padx=8, pady=(8, 4), sticky="w"
        )
        ctk.CTkLabel(frame, textvariable=self.rupees_summary_var, justify="left").grid(
            row=1, column=0, padx=8, pady=(0, 14), sticky="w"
        )

        current_card = ctk.CTkFrame(frame, corner_radius=12)
        current_card.grid(row=2, column=0, padx=8, pady=8, sticky="ew")
        current_card.grid_columnconfigure((0, 1, 2, 3), weight=1)

        ctk.CTkLabel(current_card, text="Current rupees", font=ctk.CTkFont(size=18, weight="bold")).grid(
            row=0, column=0, columnspan=4, padx=12, pady=(12, 10), sticky="w"
        )
        ctk.CTkEntry(current_card, textvariable=self.rupees_var, width=120).grid(
            row=1, column=0, padx=12, pady=(0, 12), sticky="w"
        )
        ctk.CTkButton(current_card, text="Set", width=80, command=self.apply_rupees).grid(
            row=1, column=1, padx=(0, 8), pady=(0, 12), sticky="w"
        )
        ctk.CTkButton(current_card, text="Fill wallet", width=100, command=self.fill_rupees).grid(
            row=1, column=2, padx=(0, 8), pady=(0, 12), sticky="w"
        )
        ctk.CTkButton(current_card, text="Zero", width=80, command=self.zero_rupees).grid(
            row=1, column=3, padx=(0, 12), pady=(0, 12), sticky="w"
        )

        adjust_card = ctk.CTkFrame(frame, corner_radius=12)
        adjust_card.grid(row=3, column=0, padx=8, pady=8, sticky="ew")
        adjust_card.grid_columnconfigure((0, 1, 2, 3), weight=1)

        ctk.CTkLabel(adjust_card, text="Quick adjustments", font=ctk.CTkFont(size=18, weight="bold")).grid(
            row=0, column=0, columnspan=4, padx=12, pady=(12, 10), sticky="w"
        )
        ctk.CTkButton(adjust_card, text="+ 1", command=lambda: self.adjust_rupees(1)).grid(
            row=1, column=0, padx=10, pady=(0, 12), sticky="ew"
        )
        ctk.CTkButton(adjust_card, text="+ 50", command=lambda: self.adjust_rupees(50)).grid(
            row=1, column=1, padx=10, pady=(0, 12), sticky="ew"
        )
        ctk.CTkButton(adjust_card, text="- 1", command=lambda: self.adjust_rupees(-1)).grid(
            row=1, column=2, padx=10, pady=(0, 12), sticky="ew"
        )
        ctk.CTkButton(adjust_card, text="- 50", command=lambda: self.adjust_rupees(-50)).grid(
            row=1, column=3, padx=10, pady=(0, 12), sticky="ew"
        )
