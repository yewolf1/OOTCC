# OOTCC V1

OOTCC is a Windows desktop application that connects Twitch Channel Point redeems to live gameplay actions in **Ship of Harkinian**.

The application includes:
- a CustomTkinter desktop UI
- Twitch integration through EventSub
- an overlay window for viewers
- a reward pipeline with support for temporary effects and timers
- integration with external bridge tools stored in `tools/link_state_bridge`

## Repository scope

This source repository is intended for the **Python application**.

The native bridge project is **not meant to be published in this repository**.
If you publish the sources on GitHub, keep only the Python app and exclude native bridge binaries from version control.

For a public source repository, keep:
- the Python source files
- `requirements.txt`
- `OOTCC.spec`
- `build_exe.bat`
- `make_release_zip.bat`
- `config/process_names.json`
- `config/profiles.json`
- sample Twitch config files

Do not publish:
- your real `config/twitch_config.json` if it contains private credentials
- your real `config/twitch_tokens.json`
- native bridge binaries if you want to keep them out of the public repository
- local build outputs such as `build/`, packaged `.zip` files, or generated `.exe` files

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
- `tools/link_state_bridge/...`

For public distribution, do **not** include your personal Twitch credentials.
Use sample files instead.

Recommended public config files:
- `config/twitch_config.sample.json`
- `config/twitch_tokens.sample.json`

A typical public release setup is:
- source code in the GitHub repository
- portable executable package in GitHub Releases

## Twitch configuration

The application reads Twitch configuration from JSON files in `config`.

For a public repo, provide a sample config and let users duplicate or rename it locally.
Do not commit real tokens.

## Dependencies

Runtime dependencies are listed in `requirements.txt`.

Typical dependencies include:
- `customtkinter`
- `Pillow`
- `psutil`
- `twitchAPI`

Build dependency:
- `pyinstaller`

## Notes

- End users do **not** need Python when using the packaged executable.
- The overlay and log windows are part of the application UI.
- Some rewards rely on external bridge tools, so `tools` must remain available in the portable package.
