# OOTCC 

OOTCC is a Windows desktop application that connects Twitch Channel Point redeems to live gameplay actions in **Ship of Harkinian**.

The application includes:
- a CustomTkinter desktop UI
- Twitch integration through EventSub
- Bluetooth Low Energy heart-rate integration for local chest straps and HR monitors
- an overlay window for viewers
- a reward pipeline with support for temporary effects and timers
- integration with external bridge tools stored in `tools/link_state_bridge`

## Run from source

```powershell
python -m pip install -r requirements.txt
python app.py
```

## Build the Windows executable

The project is packaged with **PyInstaller** and produces a single executable named `OOTCC.exe` at the project root.

### Build command

```powershell
.\build_exe.bat
```

After a successful build, you should get:

```text
OOTCC.exe
```

at the root of the project.

## Portable release package

The executable depends on external runtime files stored in:
- `config`
- `tools`

Because of that, the recommended release format is a **portable zip** that contains:

```text
OOTCC_portable.zip
├── OOTCC.exe
├── config/
└── tools/
```

Generate the portable zip with:

```powershell
.\make_release_zip.bat
```

## Important distribution notes

`OOTCC.exe` alone is **not enough** for end users.

To run correctly, the portable package must include:
- `OOTCC.exe`
- `config/process_names.json`
- `config/profiles.json`
- a Twitch config file
- a Bluetooth HR config file
- `tools/link_state_bridge/...`

For public distribution, do **not** include your personal Twitch credentials.
Use sample files instead.


## Twitch configuration

The application reads Twitch configuration from JSON files in `config`.

For a public repo, provide a sample config and let users duplicate or rename it locally.
Do not commit real tokens.

## Bluetooth HR configuration

The application can also read heart rate directly from a Bluetooth Low Energy device that exposes the standard Heart Rate Service.

Settings live in `config/bluetooth_hr_config.json`.

Important notes:
- Wear the chest strap before connecting.
- Moisten the electrodes so the sensor starts broadcasting valid BPM.
- Close phone fitness apps first, because many straps only allow one Bluetooth connection at a time.

Useful settings:
- `auto_connect_on_launch`
- `scan_timeout_ms`
- `reconnect_delay_ms`
- `preferred_address`
- `preferred_device_name`
- `preferred_name_substrings`
- `enemy_speed.enabled`
- `enemy_speed.command_cooldown_ms`
- `enemy_speed.levels`

Each entry in `enemy_speed.levels` uses:
- `bpm`
- `speed_percent`

## Dependencies

Runtime dependencies are listed in `requirements.txt`.

Typical dependencies include:
- `customtkinter`
- `Pillow`
- `psutil`
- `twitchAPI`

Build dependency:
- `pyinstaller`

---

# 📄 License

This project is released under the **MIT License**.  
See the `LICENSE` file for details.

---

# 🤝 Contributions

Suggestions, bug reports, UI ideas and feature requests are always welcome!  
discord server : https://discord.com/invite/EDpVBx6P5e  
discord : .yewolf  
twitch : https://www.twitch.tv/yewolf  
mail : yewolfdevandstuff@gmail.com
