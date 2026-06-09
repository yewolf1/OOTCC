@echo off
cd /d "%~dp0"

set RELEASE_NAME=OOTCC_portable
set RELEASE_DIR=%cd%\%RELEASE_NAME%

if exist "%RELEASE_DIR%" rmdir /s /q "%RELEASE_DIR%"
if exist "%cd%\%RELEASE_NAME%.zip" del /f /q "%cd%\%RELEASE_NAME%.zip"

mkdir "%RELEASE_DIR%"
mkdir "%RELEASE_DIR%\config"

copy /y ".\OOTCC.exe" "%RELEASE_DIR%\OOTCC.exe"
xcopy /e /i /y ".\tools" "%RELEASE_DIR%\tools"
copy /y ".\config\process_names.json" "%RELEASE_DIR%\config\process_names.json"
copy /y ".\config\profiles.json" "%RELEASE_DIR%\config\profiles.json"

(
echo {
echo   "channel_login": "your_channel_name",
echo   "client_id": "your_client_id",
echo   "client_secret": "your_client_secret",
echo   "scopes": [
echo     "CHANNEL_READ_REDEMPTIONS"
echo   ],
echo   "rewards": {
echo     "Kill Link": { "action": "kill_link" },
echo     "1/4 heart": { "action": "quarter_heart" },
echo     "Unequip all slots": { "action": "unequip_all_slots" },
echo     "Rupees -50": { "action": "rupees_delta", "amount": -50 },
echo     "Magic Fill": { "action": "magic_fill" },
echo     "Magic Capacity": { "action": "magic_capacity" },
echo     "Heart Fill": { "action": "heart_fill" },
echo     "Heart Capacity": { "action": "heart_capacity" },
echo     "Heart Remove Permanent": { "action": "heart_remove_permanent" },
echo     "Item Toggle": { "action": "item_toggle" },
echo     "Ammo": { "action": "ammo" },
echo     "Equipment": { "action": "equipment_toggle" },
echo     "Upgrade": { "action": "upgrade" },
echo     "Clear Buttons": { "action": "clear_buttons" },
echo     "Sword Mode": { "action": "sword_mode" },
echo     "Teleport": { "action": "teleport" },
echo     "Link Status": { "action": "link_status" },
echo     "Link Special Status": { "action": "link_special_status" },
echo     "Special Spawn": { "action": "special_spawn" },
echo     "Quest Status": { "action": "quest_status" }
echo   }
echo }
) > "%RELEASE_DIR%\config\twitch_config.json"

if exist ".\config\bluetooth_hr_config.json" (
copy /y ".\config\bluetooth_hr_config.json" "%RELEASE_DIR%\config\bluetooth_hr_config.json"
) else (
(
echo {
echo   "auto_connect_on_launch": false,
echo   "scan_timeout_ms": 8000,
echo   "reconnect_delay_ms": 3000,
echo   "preferred_address": "",
echo   "preferred_device_name": "",
echo   "preferred_name_substrings": [
echo     "H303",
echo     "MAGENE"
echo   ],
echo   "enemy_speed": {
echo     "enabled": true,
echo     "command_cooldown_ms": 2000,
echo     "levels": [
echo       { "bpm": 100, "speed_percent": 125 },
echo       { "bpm": 115, "speed_percent": 150 },
echo       { "bpm": 130, "speed_percent": 175 },
echo       { "bpm": 145, "speed_percent": 200 }
echo     ]
echo   }
echo }
) > "%RELEASE_DIR%\config\bluetooth_hr_config.json"
)

echo {}> "%RELEASE_DIR%\config\twitch_tokens.json"

powershell -NoProfile -Command "Compress-Archive -Path '%RELEASE_DIR%\*' -DestinationPath '%cd%\%RELEASE_NAME%.zip' -Force"

echo.
echo Release zip created: %cd%\%RELEASE_NAME%.zip
pause
