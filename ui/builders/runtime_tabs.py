from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

from core.definitions.inventory_definitions import BUTTON_ASSIGNABLE_ITEMS, BUTTON_LAYOUT, RANDOM_TELEPORT_DESTINATIONS, RANDOM_TELEPORT_KEYS, SWORD_BUTTON_MODES, WARP_SONG_DESTINATIONS

"""Builders for runtime-driven tabs such as magic, buttons, and teleport."""

class MainWindowRuntimeTabsBuilderMixin:
    def _build_magic_tab(self, parent: ctk.CTkFrame) -> None:
        frame = ctk.CTkScrollableFrame(parent, corner_radius=12)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(frame, text="Link magic", font=ctk.CTkFont(size=22, weight="bold")).grid(
            row=0, column=0, padx=8, pady=(8, 4), sticky="w"
        )
        ctk.CTkLabel(frame, textvariable=self.magic_summary_var, justify="left").grid(
            row=1, column=0, padx=8, pady=(0, 14), sticky="w"
        )

        current_card = ctk.CTkFrame(frame, corner_radius=12)
        current_card.grid(row=2, column=0, padx=8, pady=8, sticky="ew")
        current_card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(current_card, text="Current magic", font=ctk.CTkFont(size=18, weight="bold")).grid(
            row=0, column=0, columnspan=4, padx=12, pady=(12, 10), sticky="w"
        )
        ctk.CTkEntry(current_card, textvariable=self.magic_current_var, width=120).grid(
            row=1, column=0, padx=12, pady=(0, 12), sticky="w"
        )
        ctk.CTkButton(current_card, text="Set", width=80, command=self.apply_magic_current).grid(
            row=1, column=1, padx=(0, 8), pady=(0, 12), sticky="w"
        )
        ctk.CTkButton(current_card, text="Fill", width=80, command=self.fill_magic).grid(
            row=1, column=2, padx=(0, 8), pady=(0, 12), sticky="w"
        )
        ctk.CTkButton(current_card, text="Empty", width=80, command=self.empty_magic).grid(
            row=1, column=3, padx=(0, 12), pady=(0, 12), sticky="w"
        )

        level_card = ctk.CTkFrame(frame, corner_radius=12)
        level_card.grid(row=3, column=0, padx=8, pady=8, sticky="ew")

        ctk.CTkLabel(level_card, text="Magic meter", font=ctk.CTkFont(size=18, weight="bold")).grid(
            row=0, column=0, columnspan=2, padx=12, pady=(12, 10), sticky="w"
        )

        ctk.CTkComboBox(
            level_card,
            values=["No magic", "Normal magic", "Double magic"],
            variable=self.magic_level_var,
            width=220,
            state="readonly",
        ).grid(row=1, column=0, padx=12, pady=(0, 12), sticky="w")
        ctk.CTkButton(level_card, text="Apply", width=80, command=self.apply_magic_level).grid(
            row=1, column=1, padx=(0, 12), pady=(0, 12), sticky="w"
        )

    def _build_buttons_tab(self, parent: ctk.CTkFrame) -> None:
        scroll = ctk.CTkScrollableFrame(parent, corner_radius=12)
        scroll.pack(fill="both", expand=True, padx=10, pady=10)
        scroll.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(scroll, text="Buttons", font=ctk.CTkFont(size=22, weight="bold")).grid(
            row=0, column=0, columnspan=2, padx=8, pady=(8, 2), sticky="w"
        )
        ctk.CTkLabel(scroll, textvariable=self.button_summary_var, justify="left").grid(
            row=1, column=0, columnspan=2, padx=8, pady=(0, 14), sticky="w"
        )

        sword_card = ctk.CTkFrame(scroll, corner_radius=12)
        sword_card.grid(row=2, column=0, columnspan=2, padx=8, pady=8, sticky="ew")
        sword_card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(sword_card, text="B button / sword mode", font=ctk.CTkFont(size=18, weight="bold")).grid(
            row=0, column=0, columnspan=3, padx=12, pady=(12, 10), sticky="w"
        )
        ctk.CTkOptionMenu(
            sword_card,
            values=list(SWORD_BUTTON_MODES.values()),
            variable=self.sword_mode_var,
            state="readonly",
        ).grid(row=1, column=0, padx=12, pady=(0, 12), sticky="w")
        ctk.CTkButton(sword_card, text="Apply", width=80, command=self.apply_sword_mode).grid(
            row=1, column=1, padx=(0, 12), pady=(0, 12), sticky="w"
        )
        b_value_var = tk.StringVar(value="Unknown")
        self.button_value_vars["b"] = b_value_var
        ctk.CTkLabel(sword_card, textvariable=b_value_var, anchor="w").grid(
            row=1, column=2, padx=12, pady=(0, 12), sticky="w"
        )

        button_items = list(BUTTON_ASSIGNABLE_ITEMS.items())
        for idx, (button_key, button_label) in enumerate(BUTTON_LAYOUT[1:]):
            row = (idx // 2) + 3
            column = idx % 2
            card = ctk.CTkFrame(scroll, corner_radius=12)
            card.grid(row=row, column=column, padx=8, pady=8, sticky="nsew")
            card.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(card, text=button_label, font=ctk.CTkFont(size=18, weight="bold")).grid(
                row=0, column=0, columnspan=3, padx=12, pady=(12, 10), sticky="w"
            )

            value_var = tk.StringVar(value="Unknown")
            self.button_value_vars[button_key] = value_var
            ctk.CTkLabel(card, textvariable=value_var, anchor="w").grid(
                row=1, column=0, columnspan=3, padx=12, pady=(0, 10), sticky="w"
            )

            select_var = tk.StringVar(value=button_items[0][1])
            choice_map = {label: key for key, label in button_items}
            self.button_select_vars[button_key] = select_var
            self.button_choice_maps[button_key] = choice_map

            ctk.CTkOptionMenu(
                card,
                values=list(choice_map.keys()),
                variable=select_var,
                state="readonly",
            ).grid(row=2, column=0, padx=12, pady=(0, 12), sticky="ew")
            ctk.CTkButton(card, text="Apply", width=80, command=lambda b=button_key: self.apply_button_assignment(b)).grid(
                row=2, column=1, padx=(0, 8), pady=(0, 12)
            )
            ctk.CTkButton(card, text="Clear", width=80, command=lambda b=button_key: self.clear_button_assignment(b)).grid(
                row=2, column=2, padx=(0, 12), pady=(0, 12)
            )

    def _build_teleport_tab(self, parent: ctk.CTkFrame) -> None:
        scroll = ctk.CTkScrollableFrame(parent, corner_radius=12)
        scroll.pack(fill="both", expand=True, padx=10, pady=10)
        scroll.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(scroll, text="Runtime Teleport", font=ctk.CTkFont(size=22, weight="bold")).grid(
            row=0, column=0, columnspan=2, padx=8, pady=(8, 4), sticky="w"
        )
        ctk.CTkLabel(
            scroll,
            text=(
                "Runtime teleport uses PlayState writes only.\n"
                "The random button is intentionally limited to a conservative whitelist of non-scenario locations.\n"
                "Warp-song pads are available directly from this tab."
            ),
            justify="left",
        ).grid(row=1, column=0, columnspan=2, padx=8, pady=(0, 10), sticky="w")


        ctk.CTkLabel(scroll, textvariable=self.teleport_summary_var, justify="left").grid(
            row=2, column=0, columnspan=2, padx=8, pady=(0, 14), sticky="w"
        )

        random_card = ctk.CTkFrame(scroll, corner_radius=12)
        random_card.grid(row=3, column=0, columnspan=2, padx=8, pady=8, sticky="ew")
        random_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(random_card, text="Random safe teleport", font=ctk.CTkFont(size=18, weight="bold")).grid(
            row=0, column=0, padx=12, pady=(12, 6), sticky="w"
        )
        ctk.CTkLabel(
            random_card,
            text=f"Pool size: {len(RANDOM_TELEPORT_KEYS)} validated or conservative non-scenario destinations",
            justify="left",
        ).grid(row=1, column=0, padx=12, pady=(0, 6), sticky="w")
        ctk.CTkLabel(random_card, textvariable=self.teleport_random_result_var, justify="left").grid(
            row=2, column=0, padx=12, pady=(0, 12), sticky="w"
        )
        ctk.CTkButton(
            random_card,
            text="Random safe teleport",
            width=180,
            command=self.teleport_random_safe,
        ).grid(row=0, column=1, rowspan=3, padx=12, pady=12, sticky="e")

        ctk.CTkLabel(scroll, text="Warp song locations", font=ctk.CTkFont(size=20, weight="bold")).grid(
            row=4, column=0, columnspan=2, padx=8, pady=(16, 8), sticky="w"
        )

        current_row = 5
        for index, (destination_key, destination) in enumerate(WARP_SONG_DESTINATIONS.items()):
            card = ctk.CTkFrame(scroll, corner_radius=12)
            card.grid(row=current_row + (index // 2), column=index % 2, padx=8, pady=8, sticky="ew")
            card.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(card, text=destination["label"], font=ctk.CTkFont(size=18, weight="bold")).grid(
                row=0, column=0, padx=12, pady=(12, 6), sticky="w"
            )
            ctk.CTkLabel(
                card,
                text=(
                    f"{destination['entrance_name']}\n"
                    f"entrance 0x{destination['entrance_id']:04X} | room {destination.get('room_index', 0)}"
                ),
                justify="left",
            ).grid(row=1, column=0, padx=12, pady=(0, 8), sticky="w")

            status_var = tk.StringVar(value="Ready")
            self.teleport_status_vars[destination_key] = status_var
            ctk.CTkLabel(card, textvariable=status_var, justify="left").grid(
                row=2, column=0, padx=12, pady=(0, 10), sticky="w"
            )
            ctk.CTkButton(
                card,
                text="Teleport",
                width=120,
                command=lambda key=destination_key: self.teleport_to_warp_song(key),
            ).grid(row=0, column=1, rowspan=3, padx=12, pady=12, sticky="e")

        safe_start = current_row + ((len(WARP_SONG_DESTINATIONS) + 1) // 2)
        ctk.CTkLabel(scroll, text="Random pool preview", font=ctk.CTkFont(size=20, weight="bold")).grid(
            row=safe_start, column=0, columnspan=2, padx=8, pady=(16, 8), sticky="w"
        )

        for index, destination in enumerate(RANDOM_TELEPORT_DESTINATIONS.values(), start=1):
            label = f"• {destination['label']} (0x{destination['entrance_id']:04X})"
            ctk.CTkLabel(scroll, text=label, anchor="w", justify="left").grid(
                row=safe_start + index,
                column=(index - 1) % 2,
                padx=12,
                pady=2,
                sticky="w",
            )


    def _build_link_state_tab(self, parent: ctk.CTkFrame) -> None:
        scroll = ctk.CTkScrollableFrame(parent, corner_radius=12)
        scroll.pack(fill="both", expand=True, padx=10, pady=10)
        scroll.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(scroll, text="Link runtime states", font=ctk.CTkFont(size=22, weight="bold")).grid(
            row=0, column=0, columnspan=2, padx=8, pady=(8, 4), sticky="w"
        )
        ctk.CTkLabel(
            scroll,
            text=(
                "These actions write directly into the live Player structure.\n"
                "Set a valid runtime Player address first, then apply burn, freeze, or shock timers."
            ),
            justify="left",
        ).grid(row=1, column=0, columnspan=2, padx=8, pady=(0, 10), sticky="w")

        ctk.CTkLabel(scroll, textvariable=self.link_state_summary_var, justify="left").grid(
            row=2, column=0, columnspan=2, padx=8, pady=(0, 10), sticky="w"
        )

        bridge_card = ctk.CTkFrame(scroll, corner_radius=12)
        bridge_card.grid(row=3, column=0, columnspan=2, padx=8, pady=8, sticky="ew")
        bridge_card.grid_columnconfigure((0, 1, 2, 3), weight=1)
        ctk.CTkLabel(bridge_card, text="Standalone DLL bridge", font=ctk.CTkFont(size=18, weight="bold")).grid(
            row=0, column=0, columnspan=4, padx=12, pady=(12, 10), sticky="w"
        )
        ctk.CTkLabel(bridge_card, textvariable=self.link_bridge_summary_var, justify="left").grid(
            row=1, column=0, columnspan=4, padx=12, pady=(0, 10), sticky="w"
        )
        ctk.CTkButton(bridge_card, text="Inject / ready", width=120, command=self.ensure_dll_bridge_injected).grid(
            row=2, column=0, padx=10, pady=(0, 10), sticky="ew"
        )
        ctk.CTkButton(bridge_card, text="Burn", width=120, command=lambda: self.execute_dll_bridge_command("burn")).grid(
            row=2, column=1, padx=10, pady=(0, 10), sticky="ew"
        )
        ctk.CTkButton(bridge_card, text="Freeze", width=120, command=lambda: self.execute_dll_bridge_command("freeze")).grid(
            row=2, column=2, padx=10, pady=(0, 10), sticky="ew"
        )
        ctk.CTkButton(bridge_card, text="Shock", width=120, command=lambda: self.execute_dll_bridge_command("shock")).grid(
            row=2, column=3, padx=10, pady=(0, 10), sticky="ew"
        )
        ctk.CTkButton(bridge_card, text="Invisible on", width=120, command=lambda: self.execute_dll_bridge_command("invisible_on")).grid(
            row=3, column=0, padx=10, pady=(0, 10), sticky="ew"
        )
        ctk.CTkButton(bridge_card, text="Invisible off", width=120, command=lambda: self.execute_dll_bridge_command("invisible_off")).grid(
            row=3, column=1, padx=10, pady=(0, 10), sticky="ew"
        )
        ctk.CTkButton(bridge_card, text="Reverse on", width=120, command=lambda: self.execute_dll_bridge_command("reverse_on")).grid(
            row=3, column=2, padx=10, pady=(0, 10), sticky="ew"
        )
        ctk.CTkButton(bridge_card, text="Reverse off", width=120, command=lambda: self.execute_dll_bridge_command("reverse_off")).grid(
            row=3, column=3, padx=10, pady=(0, 10), sticky="ew"
        )
        # ctk.CTkButton(bridge_card, text="Normal", width=120, command=lambda: self.execute_dll_bridge_command("link_normal")).grid(
        #     row=4, column=0, padx=10, pady=(0, 10), sticky="ew"
        # )
        # ctk.CTkButton(bridge_card, text="Giant", width=120, command=lambda: self.execute_dll_bridge_command("link_giant")).grid(
        #     row=4, column=1, padx=10, pady=(0, 10), sticky="ew"
        # )
        # ctk.CTkButton(bridge_card, text="Minish", width=120, command=lambda: self.execute_dll_bridge_command("link_minish")).grid(
        #     row=4, column=2, padx=10, pady=(0, 10), sticky="ew"
        # )
        # ctk.CTkButton(bridge_card, text="Paper", width=120, command=lambda: self.execute_dll_bridge_command("link_paper")).grid(
        #     row=4, column=3, padx=10, pady=(0, 10), sticky="ew"
        # )
        # ctk.CTkButton(bridge_card, text="Squished", width=120, command=lambda: self.execute_dll_bridge_command("link_squished")).grid(
        #     row=5, column=0, padx=10, pady=(0, 10), sticky="ew"
        # )
        # ctk.CTkButton(bridge_card, text="Reset size", width=120, command=lambda: self.execute_dll_bridge_command("link_reset")).grid(
        #     row=5, column=1, padx=10, pady=(0, 10), sticky="ew"
        # )
        ctk.CTkButton(bridge_card, text="Lit bomb", width=120, command=lambda: self.execute_dll_bridge_command("spawn_lit_bomb")).grid(
            row=5, column=2, padx=10, pady=(0, 10), sticky="ew"
        )
        ctk.CTkButton(bridge_card, text="Bomb rain", width=120, command=lambda: self.execute_dll_bridge_command("bomb_rain")).grid(
            row=5, column=3, padx=10, pady=(0, 10), sticky="ew"
        )
        ctk.CTkButton(bridge_card, text="Explosion", width=120, command=lambda: self.execute_dll_bridge_command("spawn_explosion")).grid(
            row=6, column=0, padx=10, pady=(0, 12), sticky="ew"
        )
        ctk.CTkButton(bridge_card, text="Cucco storm", width=120, command=lambda: self.execute_dll_bridge_command("spawn_cucco_storm")).grid(
            row=6, column=1, padx=10, pady=(0, 12), sticky="ew"
        )
        ctk.CTkButton(bridge_card, text="Dark Link", width=120, command=lambda: self.execute_dll_bridge_command("spawn_darklink")).grid(
            row=6, column=2, padx=10, pady=(0, 12), sticky="ew"
        )

        address_card = ctk.CTkFrame(scroll, corner_radius=12)
        address_card.grid(row=4, column=0, columnspan=2, padx=8, pady=8, sticky="ew")
        address_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(address_card, text="Runtime Player address", font=ctk.CTkFont(size=18, weight="bold")).grid(
            row=0, column=0, columnspan=2, padx=12, pady=(12, 10), sticky="w"
        )
        ctk.CTkEntry(address_card, textvariable=self.link_player_address_var).grid(
            row=1, column=0, padx=12, pady=(0, 12), sticky="ew"
        )
        ctk.CTkButton(address_card, text="Apply", width=100, command=self.apply_link_state_player_address).grid(
            row=1, column=1, padx=(0, 12), pady=(0, 12), sticky="e"
        )

        burn_card = ctk.CTkFrame(scroll, corner_radius=12)
        burn_card.grid(row=5, column=0, padx=8, pady=8, sticky="nsew")
        burn_card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(burn_card, text="Burn", font=ctk.CTkFont(size=18, weight="bold")).grid(
            row=0, column=0, columnspan=2, padx=12, pady=(12, 10), sticky="w"
        )
        ctk.CTkEntry(burn_card, textvariable=self.link_burn_value_var, width=120).grid(
            row=1, column=0, padx=12, pady=(0, 12), sticky="w"
        )
        ctk.CTkButton(burn_card, text="Apply burn", width=120, command=self.apply_link_burn).grid(
            row=1, column=1, padx=(0, 12), pady=(0, 12), sticky="e"
        )
        ctk.CTkButton(burn_card, text="Clear burn", width=120, command=self.clear_link_burn).grid(
            row=2, column=1, padx=(0, 12), pady=(0, 12), sticky="e"
        )

        freeze_card = ctk.CTkFrame(scroll, corner_radius=12)
        freeze_card.grid(row=5, column=1, padx=8, pady=8, sticky="nsew")
        freeze_card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(freeze_card, text="Freeze / Shock", font=ctk.CTkFont(size=18, weight="bold")).grid(
            row=0, column=0, columnspan=2, padx=12, pady=(12, 10), sticky="w"
        )
        ctk.CTkLabel(freeze_card, text="Freeze timer").grid(row=1, column=0, padx=12, pady=(0, 6), sticky="w")
        ctk.CTkEntry(freeze_card, textvariable=self.link_freeze_value_var, width=120).grid(
            row=1, column=1, padx=(0, 12), pady=(0, 6), sticky="e"
        )
        ctk.CTkButton(freeze_card, text="Apply freeze", width=120, command=self.apply_link_freeze).grid(
            row=2, column=1, padx=(0, 12), pady=(0, 12), sticky="e"
        )
        ctk.CTkLabel(freeze_card, text="Shock timer").grid(row=3, column=0, padx=12, pady=(0, 6), sticky="w")
        ctk.CTkEntry(freeze_card, textvariable=self.link_shock_value_var, width=120).grid(
            row=3, column=1, padx=(0, 12), pady=(0, 6), sticky="e"
        )
        ctk.CTkButton(freeze_card, text="Apply shock", width=120, command=self.apply_link_shock).grid(
            row=4, column=1, padx=(0, 12), pady=(0, 12), sticky="e"
        )
